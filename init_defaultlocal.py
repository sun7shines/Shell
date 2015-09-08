import os,sys
import stat
import shutil
import time
import subprocess
import re

def check_defaultlocal():
    cmd=["vgdisplay"]
    output=subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=open('/dev/null','w'))
    out = output.stdout.read()
    if out.find("defaultlocal")==-1:
        return False
    else:
        return True
def zero_disk(device):
    cmd = "dd if=/dev/zero of="+device+" bs=64 count=1024"
    os.system(cmd)
    cmd = "partprobe -s "+device
    os.system(cmd)
def make_partition(device):
    cmd="parted -s "+device+" mklabel msdos >/dev/null 2>&1"
    os.system(cmd)

    start=['1MB','500MB']
    end=['500MB','16500MB']
    cmd = "parted -s "+device+" mkpart primary "+start[0]+" "+end[0]
    os.system(cmd)
    cmd = "parted -s "+device+" mkpart primary "+start[1]+" "+end[1]
    os.system(cmd)

    cmd = "mkfs -t ext3 "+device+"1"
    os.system(cmd)
    cmd = "mkfs -t ext3 "+device+"2"
    os.system(cmd)
def get_partition_info(device):
    cmd = ['parted','-s','-l']
    output=subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=open('/dev/null', 'w')
                            )

    out = output.stdout.read()
    flag=0
    flag_device=-1
    device_info=[] 
    lines=out.split("\n")
    for line in lines:
        if line.startswith("Disk "):
            flag=flag+1
        if line.startswith("Disk "+device):
            flag_device=flag
        if flag==flag_device:
            #print line
            device_info.append(line)
    #print device_info            
    
    part_flag=0
    part_info=[]
    for line in device_info:
        if line=='':
            part_flag=0
        if part_flag==1:
            part_info.append(line)
        if line.startswith("Number"):
            part_flag=1
    #print part_info
    return part_info
def get_device_size_by_MB(device):
    cmd = ['parted','-s','-l']
    output=subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=open('/dev/null', 'w')
                            )

    out = output.stdout.read()
    flag=0
    flag_device=-1
    device_info=[]
    lines=out.split("\n")
    str=None
    flag_line=None
    for line in lines:
        if line.startswith("Disk "+device):
            str=re.findall("[0-9]+\.*[0-9]+",line)
            flag_line=line
    n=float(str[0])
    n1=int(n)
    #print n1

    str=flag_line
    f=n1-1
    if str.find("kB")!=-1:
        f=f/1000
    if str.find("MB")!=-1:
        f=f
    if str.find("GB")!=-1:
        f=f*1000
    size=f
    print size
    return size
def get_used_partition_by_MB(part_info):
    start=[]
    end=[]
    for line in part_info:
        str=line.split()   
        start.append(str[1])
        end.append(str[2])
    print start
    print end 
    list=[]
    int_start=[]
    int_end=[]
    for str in start:
        f=0
        if str.find("kB")!=-1:
            f=float(str[:-2])
            f=f/1000
        if str.find("MB")!=-1:
            f=float(str[:-2])
        if str.find("GB")!=-1:
            f=float(str[:-2])
            f=f*1000
        int_start.append(f)
    print int_start
   
    for str in end:
        f=0
        if str.find("kB")!=-1:
            f=float(str[:-2])
            f=f/1000
        if str.find("MB")!=-1:
            f=float(str[:-2])
        if str.find("GB")!=-1:
            f=float(str[:-2])
            f=f*1000
        int_end.append(f)
    print int_end 
    list.append(int_start)
    list.append(int_end)
    return list
def get_unused_spaces_by_MB(list,size):
    u_list=[]
    u_start=[]
    u_end=[]
    start=list[0]
    end=list[1]
    l=len(start)
    i=1
    if 1!=start[0]:
        u_start.append(1)
        u_end.append(start[0])
    while i<=(l-1):
        if end[i-1]==start[i]:
            i=i+1
            continue
        else:
            u_start.append(end[i-1])
            u_end.append(start[i])
            i=i+1
    if end[i-1]<size:
        u_start.append(end[i-1])
        u_end.append(size)
    print u_start
    print u_end
    u_list.append(u_start)
    u_list.append(u_end)
    return u_list
def get_useful_spaces_list(list):
    #limit=2*1000*1000
    limit=50*1000
    start=list[0]
    end=list[1]
    l=len(start)
    i=0
    while i<=(l-1):
        if end[i]-start[i]<512:
            end[i]=-1
            start[i]=-1
        i=i+1
    
    new_start=[]
    new_end=[]
    l=len(start)
    i=0
    while i<=l-1:
        while end[i]-start[i]>=limit:
            new_start.append(start[i])
            new_end.append(start[i]+limit)
            start[i]=start[i]+limit
        if end[i]-start[i]<512:
            end[i]=-1
            start[i]=-1
        new_start.append(start[i]) 
        new_end.append(end[i])
        i=i+1
    l = len(new_start)
    i=0
    while i<=l-1:
        if new_start[i]==-1:
            del new_start[i]
            del new_end[i]
            l = l-1
            continue
        else:
            i=i+1
    print new_start
    print new_end  
    new_list=[]
    new_list.append(new_start)  
    new_list.append(new_end)
    return new_list
   
def get_partition_list(device):
    part_info=get_partition_info(device)
    list=get_used_partition_by_MB(part_info)
    size=get_device_size_by_MB(device)
    u_list=get_unused_spaces_by_MB(list,size)
    list_1=get_useful_spaces_list(u_list)
    start_1=list_1[0]
    end_1=list_1[1]
    l = len(list[0])
    num = l
    l = 4-l
    i =0 
    start_2=[]
    end_2=[]
    l1=len(start_1)
    if l1<l:
        l=l1
    while i<= l-1:
        start_2.append(start_1[i])    
        end_2.append(end_1[i])
        i=i+1
    list_2=[]
    list_2.append(start_2) 
    list_2.append(end_2)
    list_2.append(num)
    return list_2
def create_defaultlocal(device,num,start,end):
    cmd = "parted -s "+device+" mkpart primary "+start+" "+end
    os.system(cmd)
    cmd="partprobe -s "+device
    os.system(cmd)
    dev= device+str(num)
    cmd = "pvcreate "+dev+" >/dev/null 2>&1"
    os.system(cmd)
    cmd="vgcreate /dev/defaultlocal "+dev
    os.system(cmd)
    cmd="vgchange -a y /dev/defaultlocal"
    os.system(cmd)

    """size1="100MB"
    cmd= "lvcreate -n /dev/defaultlocal/defaultlocal -L "+size1+" defaultlocal"
    os.system(cmd)

    cmd = "lvextend /dev/defaultlocal/defaultlocal "+dev
    os.system(cmd)
    cmd="lvdisplay"
    os.system(cmd)"""

    return dev
def extend_defaultlocal(device,num,start,end):
    cmd = "parted -s "+device+" mkpart primary "+start+" "+end
    os.system(cmd)
    cmd="partprobe -s "+device
    os.system(cmd)
    dev= device+str(num)
    cmd = "pvcreate "+dev
    os.system(cmd)
    cmd = "vgextend /dev/defaultlocal "+dev
    os.system(cmd)
    cmd = "lvextend /dev/defaultlocal/defaultlocal "+dev
    os.system(cmd)
    return dev
def delete_defaultlocal():
    cmd= "vgremove /dev/defaultlocal -f"
    os.system(cmd)
    cmd = "pvremove /dev/sdc3 -f"
    os.system(cmd)
    cmd = "pvremove /dev/sdc4 -f"
    os.system(cmd)
def init_defaultlocal(device):
    list=get_partition_list(device)
    start=list[0]
    end=list[1]
    num=list[2]
    print start
    print end
    l = len(start)
    if l==0:
        print "alread exist 4 partition" 
    i=0
    num = num+1
    devs=[]
    while i<=l-1:
        if check_defaultlocal():
            x=extend_defaultlocal(device,num,str(start[i]),str(end[i]))
            devs.append(x)
            num = num+1
        else:
            x=create_defaultlocal(device,num,str(start[i]),str(end[i]))
            devs.append(x)
            num = num+1
        i=i+1

    size1="100MB"
    cmd= "lvcreate -n /dev/defaultlocal/defaultlocal -L "+size1+" defaultlocal"
    os.system(cmd)
    for dev in devs:
        cmd = "lvextend /dev/defaultlocal/defaultlocal "+dev
        os.system(cmd)
    cmd="lvdisplay"
    os.system(cmd)
    cmd = "mkfs.ext4 /dev/defaultlocal/defaultlocal"     
    os.system(cmd)
if __name__=="__main__":
    device="/dev/sdc"
    if sys.argv[1]=="1":
        if check_defaultlocal():
            delete_defaultlocal()
        zero_disk(device)
        make_partition(device)
    if sys.argv[1]=="2":
        if check_defaultlocal():
            print "defaultlocal exist"
        else:
            print "defaultlocal not exist"
    if sys.argv[1]=="3":
        get_partition_info(device)
    if sys.argv[1]=="4":
        get_device_size_by_MB(device)
    if sys.argv[1]=="5":
        part_info=get_partition_info(device)
        get_used_partition_by_MB(part_info)
    if sys.argv[1]=="6":
        part_info=get_partition_info(device)
        list=get_used_partition_by_MB(part_info)
        size=get_device_size_by_MB(device)
        u_list=get_unused_spaces_by_MB(list,size)
        get_useful_spaces_list(u_list)
    if sys.argv[1]=="7":
        get_partition_list(device)
    if sys.argv[1]=="8":
        init_defaultlocal(device)
    if sys.argv[1]=="9":
        pass
