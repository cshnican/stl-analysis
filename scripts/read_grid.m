#import <Foundation/Foundation.h>
#import <AppKit/AppKit.h>
static unsigned char *B; static int ST, IMG_W, IMG_H;
static NSBitmapImageRep *HOLD;
static int lightAt(int x,int y){
    unsigned char *p=B+y*ST+x*4; return (p[0]+p[1]+p[2])>400;
}
static int orangeAt(int x,int y){
    unsigned char *p=B+y*ST+x*4; int r=p[0],g=p[1],b=p[2];
    return r>175 && g>85 && b<170 && r>g+25;
}
enum { TW=10, TH=16, TS=TW*TH };
static int load(const char *path){
    NSImage *img=[[NSImage alloc] initWithContentsOfFile:@(path)];
    if(!img){ fprintf(stderr,"no image %s\n", path); return 0; }
    HOLD=[[NSBitmapImageRep alloc] initWithData:[img TIFFRepresentation]];
    if(!HOLD){ fprintf(stderr,"no rep\n"); return 0; }
    B=HOLD.bitmapData; ST=(int)HOLD.bytesPerRow; IMG_W=(int)HOLD.pixelsWide; IMG_H=(int)HOLD.pixelsHigh;
    fprintf(stderr,"loaded %s %dx%d\n", path, IMG_W, IMG_H);
    return 1;
}
static void stamp(int x0,int x1,int y0,int y1, unsigned char *out, int *kind){
    memset(out,0,TS); *kind=0;
    if(x0<0)x0=0; if(y0<0)y0=0; if(x1>IMG_W)x1=IMG_W; if(y1>IMG_H)y1=IMG_H;
    int area=(x1-x0)*(y1-y0); if(area<1) return;
    int oc=0, lc=0, X0=9999,Y0=9999,X1=-1,Y1=-1;
    for(int y=y0;y<y1;y++) for(int x=x0;x<x1;x++){
        if(orangeAt(x,y)) oc++;
        if(lightAt(x,y)){ lc++; if(x<X0)X0=x; if(y<Y0)Y0=y; if(x>X1)X1=x; if(y>Y1)Y1=y; }
    }
    if(oc*5 > area){ *kind=12; return; }
    if(lc*40 < area){ *kind=0; return; }
    int bw=X1-X0+1, bh=Y1-Y0+1;
    if(bw > bh){ *kind=10; return; }
    *kind=1;
    for(int oy=0;oy<TH;oy++) for(int ox=0;ox<TW;ox++){
        int xa=X0+bw*ox/TW, xb=X0+bw*(ox+1)/TW; if(xb<=xa) xb=xa+1;
        int ya=Y0+bh*oy/TH, yb=Y0+bh*(oy+1)/TH; if(yb<=ya) yb=ya+1;
        int c=0,n=0;
        for(int y=ya;y<yb && y<=Y1;y++) for(int x=xa;x<xb && x<=X1;x++){ n++; if(lightAt(x,y)) c++; }
        out[oy*TW+ox]=(n && c*2>=n);
    }
}
static int ham(unsigned char *a, unsigned char *b){ int d=0; for(int i=0;i<TS;i++) d+=a[i]!=b[i]; return d; }
int main(int argc, const char **argv){@autoreleasepool{
    fprintf(stderr,"argc %d\n", argc);
    if(argc<4){ fprintf(stderr,"usage: read_grid template.jpg image coords\n"); return 1; }
    if(!load(argv[1])) return 1;
    int ys41[]={83,115,147,179,211,244,276,308,340,372,405,437,469,501,533,566,598,630,662,695,727,759,791,824,856,888,920,952,985,1017,1049};
    int trow[]={2,11,4,20,7,17,27,5};
    int tval[]={2,3,4,5,6,7,8,1};
    unsigned char tmpl[8][TS];
    for(int t=0;t<8;t++){
        int kind; int r=trow[t]-1;
        stamp(359,390, ys41[r]+2, ys41[r+1]-2, tmpl[t], &kind);
        fprintf(stderr,"template %d kind %d\n", tval[t], kind);
        if(kind!=1) return 1;
    }
    // copy templates off the image
    unsigned char tmplcopy[8][TS];
    memcpy(tmplcopy, tmpl, sizeof(tmpl));
    if(!load(argv[2])) return 1;
    FILE *cf=fopen(argv[3],"r");
    int nc,nr; fscanf(cf,"%d %d",&nc,&nr);
    int xs[40], ys[50];
    for(int i=0;i<=nc;i++) fscanf(cf,"%d",&xs[i]);
    for(int i=0;i<=nr;i++) fscanf(cf,"%d",&ys[i]);
    fclose(cf);
    fprintf(stderr,"grid %d x %d x0 %d y0 %d\n", nc, nr, xs[0], ys[0]);
    fprintf(stderr,"x0 %d xlast %d y0 %d ylast %d\n", xs[0], xs[nc], ys[0], ys[nr]);
    for(int r=0;r<nr;r++){
        int sum=0;
        printf("R%02d", r+1);
        for(int c=0;c<nc;c++){
            unsigned char bits[TS]; int kind;
            stamp(xs[c]+6, xs[c+1]-6, ys[r]+5, ys[r+1]-4, bits, &kind);
            int v=0;
            if(kind==12||kind==10||kind==0) v=kind;
            else {
                int best=999, bi=0;
                for(int t=0;t<8;t++){ int d=ham(bits,tmplcopy[t]); if(d<best){ best=d; bi=t; } }
                v=tval[bi];
            }
            if(v>0) sum+=v;
            if(v==0) printf("\t."); else printf("\t%d", v);
        }
        printf("\t=%d\n", sum);
    }
    return 0;
}}
