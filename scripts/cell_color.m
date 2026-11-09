#import <Foundation/Foundation.h>
#import <AppKit/AppKit.h>
// Per-cell color on a photo, so a red 10 is not kept as an orange 12.
int main(int argc, const char **argv){@autoreleasepool{
    NSImage *img=[[NSImage alloc] initWithContentsOfFile:@(argv[1])];
    NSBitmapImageRep *rep=[[NSBitmapImageRep alloc] initWithData:[img TIFFRepresentation]];
    unsigned char *B=rep.bitmapData; int ST=(int)rep.bytesPerRow, W=(int)rep.pixelsWide, H=(int)rep.pixelsHigh;
    FILE *cf=fopen(argv[2],"r");
    int nc,nr; fscanf(cf,"%d %d",&nc,&nr);
    int xs[80], ys[80];
    for(int i=0;i<=nc;i++) fscanf(cf,"%d",&xs[i]);
    for(int i=0;i<=nr;i++) fscanf(cf,"%d",&ys[i]);
    fclose(cf);
    for(int r=0;r<nr;r++) for(int c=0;c<nc;c++){
        int x0=xs[c]+4, x1=xs[c+1]-4, y0=ys[r]+4, y1=ys[r+1]-3;
        if(x0<0)x0=0; if(y0<0)y0=0; if(x1>W)x1=W; if(y1>H)y1=H;
        long sum=0, light=0, red=0, yel=0, n=0;
        for(int y=y0;y<y1;y++) for(int x=x0;x<x1;x++){
            unsigned char *p=B+y*ST+x*4; int R=p[0],G=p[1],Bl=p[2];
            int s=R+G+Bl; sum+=s; n++;
            if(s>420) light++;
            if(R>140 && R>G+30 && Bl<140) red++;
            if(R>160 && G>120 && G>Bl+20) yel++;
        }
        if(!n) continue;
        printf("%d %d %ld %ld %ld %ld\n", r, c, sum/n, light*100/n, red*100/n, yel*100/n);
    }
}}
