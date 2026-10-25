#define COBJMACROS
#include <windows.h>
#include <mmdeviceapi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "wine/list.h"
typedef struct MMDevice {IMMDevice IMMDevice_iface; struct list entry; EDataFlow flow; GUID devguid; LONG refs;} MMDevice;
struct endpoint {unsigned name,device;};
struct get_endpoint_ids_params {EDataFlow flow;struct endpoint *endpoints;unsigned size;HRESULT result;unsigned num,default_idx;};
static struct list device_list=LIST_INIT(device_list);
static CRITICAL_SECTION detroit_device_lock={NULL,-1,0,0,0,0};
static struct {int module_unixlib;} drvs;
static int choice, mode, creations, formats, calls;
#define TRACE(...) ((void)0)
#define get_endpoint_ids 0
static ULONG WINAPI addref(IMMDevice *p){return InterlockedIncrement(&((MMDevice*)p)->refs);}
static ULONG WINAPI release(IMMDevice *p){return InterlockedDecrement(&((MMDevice*)p)->refs);}
static IMMDeviceVtbl vtbl={.AddRef=addref,.Release=release};
static void get_device_guid(EDataFlow f,const char *name,GUID *g){memset(g,0,sizeof(*g));g->Data1=atoi(name);}
static MMDevice *MMDevice_Create(const WCHAR *n,GUID *g,EDataFlow f,DWORD state,BOOL def){
 MMDevice *p=calloc(1,sizeof(*p));p->IMMDevice_iface.lpVtbl=&vtbl;p->flow=f;p->devguid=*g;list_add_tail(&device_list,&p->entry);creations++;return p;
}
static HRESULT set_format(MMDevice *p){formats++;return S_OK;}
static void backend(int lib,int op,struct get_endpoint_ids_params *p){
 const WCHAR name[]=L"output";calls++;
 if(mode==1){p->result=E_FAIL;return;}
 if(mode==2){p->num=0;p->result=S_OK;return;}
 if(mode==3 && p->size<2048){p->size=2048;p->result=HRESULT_FROM_WIN32(ERROR_INSUFFICIENT_BUFFER);return;}
 p->num=2;p->default_idx=choice;p->result=S_OK;
 for(int i=0;i<2;i++){p->endpoints[i].name=32+i*32;p->endpoints[i].device=100+i*8;memcpy((char*)p->endpoints+p->endpoints[i].name,name,sizeof(name));sprintf((char*)p->endpoints+p->endpoints[i].device,"%d",i+1);}
}
#define __wine_unix_call backend
#include "endpoint-under-test.inc"
static DWORD WINAPI repeat(void *arg){for(int i=0;i<100;i++){IMMDevice *d=NULL;assert(SUCCEEDED(detroit_default_render_device(&d)));assert(((MMDevice*)d)->devguid.Data1==2);IMMDevice_Release(d);}return 0;}
int main(void){
 IMMDevice *a=NULL,*b=NULL;assert(SUCCEEDED(detroit_default_render_device(&a)));assert(creations==1);
 assert(SUCCEEDED(detroit_default_render_device(&b)));assert(a==b&&creations==1);IMMDevice_Release(b);
 choice=1;assert(SUCCEEDED(detroit_default_render_device(&b)));assert(a!=b&&creations==2&&((MMDevice*)a)->devguid.Data1==1);IMMDevice_Release(a);IMMDevice_Release(b);
 mode=1;b=NULL;assert(FAILED(detroit_default_render_device(&b))&&b==NULL);
 mode=2;assert(detroit_default_render_device(&b)==E_NOTFOUND&&b==NULL);
 mode=3;calls=0;assert(SUCCEEDED(detroit_default_render_device(&b))&&calls==2);IMMDevice_Release(b);
 mode=0;HANDLE threads[2];for(int i=0;i<2;i++)threads[i]=CreateThread(NULL,0,repeat,NULL,0,NULL);WaitForMultipleObjects(2,threads,TRUE,INFINITE);for(int i=0;i<2;i++)CloseHandle(threads[i]);
 assert(creations==2&&formats==2);MMDevice *p,*next;LIST_FOR_EACH_ENTRY_SAFE(p,next,&device_list,MMDevice,entry){assert(p->refs==0);list_remove(&p->entry);free(p);}
 puts("endpoint default-change, identity, failure, absence, resize, concurrent reuse: PASS");return 0;
}
