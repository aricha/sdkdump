#!/usr/bin/env python
import argparse
import os, sys
from os import path
import multiprocessing
import subprocess

DEBUG = False

DEFAULT_SDK = 'iphonesimulator'
FRAMEWORK_DIRS = ['Frameworks', 'PrivateFrameworks']
OPTIONAL_BINARIES = {
    'SpringBoard': path.join('CoreServices', 'SpringBoard.app', 'SpringBoard')
}

class Binary:
    def __init__(self, binaryPath):
        self.path = binaryPath
        self.name = path.basename(binaryPath)
        self.frameworkPath = path.dirname(binaryPath)

def getSDKPath(sdk):
    def getXcodebuildValue(output, key):
        for l in output.splitlines():
            si = l.find(key)
            if si == -1:
                continue
            ei = si + len(key)
            return l[ei:].strip()

    try:
        with open(os.devnull, 'w') as devnull:
            output = subprocess.check_output(['xcodebuild', '-version', '-sdk', sdk], stderr=devnull)
        return getXcodebuildValue(output, 'Path:')
    except subprocess.CalledProcessError, e:
        if DEBUG: print 'Error running xcodebuild:', e.output
        return None

def frameworkBinaryIter(sdkPath):
    slibPath = path.join(sdkPath, 'System', 'Library')

    def newBinary(binaryPath, category):
        binary = Binary(binaryPath)
        binary.category = category

        def fwkChainIter():
            pathComponents = path.relpath(binaryPath, slibPath).split(os.sep)
            for component in pathComponents:
                name, ext = path.splitext(component)
                if ext == '.framework':
                    yield name
        binary.frameworkChain = list(fwkChainIter())

        return binary
            
    for category in FRAMEWORK_DIRS:
        fwkContainer = path.join(slibPath, category)
        if not path.exists(fwkContainer):
            print 'Error: framework path "', fwkContainer, '" not found'
            continue

        # need to do a recursive walk to handle nested frameworks
        for fwkPath, _, _ in os.walk(fwkContainer):
            basedir = path.basename(fwkPath)
            fwkName, ext = path.splitext(basedir)
            if not path.isdir(fwkPath) or ext != '.framework':
                continue
            
            binaryPath = path.join(fwkPath, fwkName)
            if path.isfile(binaryPath):
                yield newBinary(binaryPath, category)

    for name, relativePath in OPTIONAL_BINARIES.iteritems():
        binaryPath = path.join(slibPath, relativePath)
        if path.isfile(binaryPath):
            yield newBinary(binaryPath, name)
        else:
            print 'Could not find', name, 'in', relativePath

def dumpBinary(info):
    binary = info['binary']
    outputDir = info['outputDir']
    fwkOutput = path.join(outputDir, binary.category, *binary.frameworkChain)

    if DEBUG: print 'Dumping framework', binary.name, 'to path', fwkOutput
    subprocess.call(['class-dump', '-H', '-o', fwkOutput, binary.path])

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Dump SDK header files')
    arg_parser.add_argument('-s', dest='sdk', help='The SDK version to use (eg. iphoneos7.1)')
    arg_parser.add_argument('-o', dest='output', help='The output directory (defaults to the current directory)')

    args = arg_parser.parse_args()
    outdir = path.abspath(args.output) or os.getcwd()
    sdk = args.sdk or DEFAULT_SDK

    sdkPath = getSDKPath(sdk)
    if not sdkPath:
        sys.exit('Error finding SDK %s' % sdk)

    # Parallelize class-dump work
    dumpIter = ({'binary': binary, 'outputDir': outdir} 
        for binary in frameworkBinaryIter(sdkPath))
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    pool.map(dumpBinary, dumpIter)
