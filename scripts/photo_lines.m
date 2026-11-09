#import <Foundation/Foundation.h>
#import <AppKit/AppKit.h>
// Bright ridges on a monitor photo. Grid lines are the local luminance peaks.
// argv: image y0 y1 x0 x1
int main(int argc, const char **argv){@autoreleasepool{
    if(argc<6) return 1;
    NSImage *img=[[NSImage alloc] initWithContentsOfFile:@(argv[1])];
    NSBitmapImageRep *rep=[[NSBitmapImageRep alloc] initWithData:[img TIFFRepresentation]];
    unsigned char *B=rep.bitmapData; int ST=(int)rep.bytesPerRow;
    int W=(int)rep.pixelsWide, H=(int)rep.pixelsHigh;
    int y0=atoi(argv[2]), y1=atoi(argv[3]), x0=atoi(argv[4]), x1=atoi(argv[5]);
    if(y0<0) y0=0; if(x0<0) x0=0; if(y1>H) y1=H; if(x1>W) x1=W;
    printf("SIZE %d %d\n", W, H);
    double *col=calloc(W, sizeof(double));
    for(int x=0;x<W;x++){
        long s=0, n=0;
        for(int y=y0;y<y1;y+=2){
            unsigned char *p=B+y*ST+x*4;
            s+=p[0]+p[1]+p[2]; n++;
        }
        col[x]=n? (double)s/n : 0;
    }
    printf("V\n");
    for(int x=2;x<W-2;x++){
        double here=col[x], nb=(col[x-2]+col[x+2])/2;
        if(here>nb+12 && here>col[x-1] && here>=col[x+1] && here>80)
            printf("%d %.0f %.0f\n", x, here, here-nb);
    }
    free(col);
    double *row=calloc(H, sizeof(double));
    for(int y=0;y<H;y++){
        long s=0, n=0;
        for(int x=x0;x<x1;x+=2){
            unsigned char *p=B+y*ST+x*4;
            s+=p[0]+p[1]+p[2]; n++;
        }
        row[y]=n? (double)s/n : 0;
    }
    printf("H\n");
    for(int y=2;y<H-2;y++){
        double here=row[y], nb=(row[y-2]+row[y+2])/2;
        if(here>nb+8 && here>row[y-1] && here>=row[y+1] && here>70)
            printf("%d %.0f %.0f\n", y, here, here-nb);
    }
    free(row);
}}
