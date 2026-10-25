// Loads compiled libraries without starting Wine, a game or a render pipeline.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (argc != 2 && !(argc == 3 && strcmp(argv[1], "--list-file") == 0)) {
            fprintf(stderr, "Usage: metal-library-probe library.metallib | --list-file paths.txt\n");
            return 2;
        }
        id<MTLDevice> device = MTLCreateSystemDefaultDevice();
        if (!device) {
            fprintf(stderr, "No Metal device\n");
            return 3;
        }
        NSArray<NSString *> *paths;
        if (argc == 3) {
            NSError *error = nil;
            NSString *list = [NSString stringWithContentsOfFile:[NSString stringWithUTF8String:argv[2]]
                                                     encoding:NSUTF8StringEncoding error:&error];
            if (!list) {
                fprintf(stderr, "Cannot read list: %s\n", error.localizedDescription.UTF8String);
                return 2;
            }
            paths = [list componentsSeparatedByString:@"\n"];
        } else {
            paths = @[[NSString stringWithUTF8String:argv[1]]];
        }
        NSUInteger loaded = 0, failed = 0, functions = 0;
        for (NSString *path in paths) {
            if (!path.length) { continue; }
            @autoreleasepool {
                NSError *error = nil;
                id<MTLLibrary> library = [device newLibraryWithURL:[NSURL fileURLWithPath:path] error:&error];
                if (!library || library.functionNames.count == 0) {
                    fprintf(stderr, "Library rejected: %s: %s\n", path.UTF8String,
                            error ? error.localizedDescription.UTF8String : "no functions");
                    failed++;
                } else {
                    loaded++;
                    functions += library.functionNames.count;
                }
            }
        }
        printf("Libraries accepted=%lu rejected=%lu functions=%lu\n",
               (unsigned long)loaded, (unsigned long)failed, (unsigned long)functions);
        return failed ? 4 : (loaded ? 0 : 5);
    }
}
