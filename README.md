# sdkdump

A simple tool for dumping the header files of all frameworks in the iOS or OS X SDK in a single step (all Frameworks, PrivateFrameworks, and SpringBoard, if available). Requires that [class-dump](https://github.com/nygard/class-dump) be installed to work.

Usage:

```sh
sdkdump.py [-s <sdk>] [-o <output_dir>]
```

Where `<sdk>` is the SDK ID used by `xcodebuild`, such as `iphoneos7.1`, `iphonesimulator`, or `macosx10.9`. Run `xcodebuild -version -sdk` to see what SDKs you currently have installed.