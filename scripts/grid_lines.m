#import <Foundation/Foundation.h>
#import <AppKit/AppKit.h>
int main(int argc, const char **argv){@autoreleasepool{
    NSImage *img=[[NSImage alloc] initWithContentsOfFile:@(argv[1])];
    NSBitmapImageRep *rep=[[NSBitmapImageRep alloc] initWithData:[img TIFFRepresentation]];
    unsigned char *B=rep.bitmapData; int ST=(int)rep.bytesPerRow, W=(int)rep.pixelsWide, H=(int)rep.pixelsHigh;
    printf("SIZE %d %d\nV\n", W, H);
    int run=0, best=0, bestat=0;
    for(int x=W/5;x<W;x++){
        int dots=0;
        for(int y=H/12;y<H*11/12;y+=2){
            unsigned char *p=B+y*ST+x*4; int r=p[0],g=p[1],b=p[2];
            if(r>55 && r<210 && abs(r-g)<45 && abs(g-(int)b)<45) dots++;
        }
        if(dots>40){ if(dots>best){ best=dots; bestat=x; } run=1; }
        else if(run){ printf("%d %d\n", bestat, best); run=0; best=0; }
    }
    if(run) printf("%d %d\n", bestat, best);
    printf("H\n");
    run=0; best=0; bestat=0;
    for(int y=0;y<H;y++){
        int dots=0;
        for(int x=W/3;x<W*19/20;x+=2){
            unsigned char *p=B+y*ST+x*4; int r=p[0],g=p[1],b=p[2];
            if(r>55 && r<210 && abs(r-g)<45 && abs(g-(int)b)<45) dots++;
        }
        if(dots>25){ if(dots>best){ best=dots; bestat=y; } run=1; }
        else if(run){ printf("%d %d\n", bestat, best); run=0; best=0; }
    }
    if(run) printf("%d %d\n", bestat, best);
}}
