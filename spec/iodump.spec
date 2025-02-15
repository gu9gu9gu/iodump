%global __os_install_post %{nil}
%define _ignore_post_scripts_errors %{nil}
%define current_kver   %{?kver}%{!?kver:%(rpm -qa kernel-devel | head -n 1 | sed 's/^kernel-devel-//')}
%define kver_name      %(echo %{current_kver} | awk -F. '{print substr($0,0,index($0,$(NF-1))-2)}')
%define bare_name      iodump
%define anolis_release 6

Name:                  %{bare_name}-%{kver_name}
Version:               1.0.1
Release:               %{anolis_release}%{?dist}
Url:                   https://gitee.com/anolis/iodump.git
Summary:               io details
Group:                 System Environment/Base
License:               MIT
Source0:               %{bare_name}-%{version}.tar.gz

Vendor:                Alibaba

BuildRequires: elfutils-devel

# Add debug package
%debug_package

%description
dump the io details 

%prep
cd $RPM_BUILD_DIR
rm -rf %{bare_name}-%{version}
gzip -dc $RPM_SOURCE_DIR/%{bare_name}-%{version}.tar.gz | tar -xvvf -
if [ $? -ne 0 ]; then
    exit $?
fi
main_dir=$(tar -tzvf $RPM_SOURCE_DIR/%{bare_name}-%{version}.tar.gz| head -n 1 | awk '{print $NF}' | awk -F/ '{print $1}')
if [ "${main_dir}" == %{bare_name} ];then
    mv %{bare_name} %{bare_name}-%{version}
fi
cd %{bare_name}-%{version}
chmod -R a+rX,u+w,g-w,o-w .
 
%build
cd %{bare_name}-%{version}
make

%install
BuildDir=$RPM_BUILD_DIR/%{bare_name}-%{version}
install -d                             %{buildroot}/usr/lib/iodump/
install $BuildDir/kernel/kiodump.ko    %{buildroot}/usr/lib/iodump/kiodump.ko
install -d                             %{buildroot}/usr/src/os_health/iodump/
install $BuildDir/kernel/kiodump.conf  %{buildroot}/usr/src/os_health/iodump/kiodump.conf
install -d                             %{buildroot}/usr/sbin/
install $BuildDir/user/iodump          %{buildroot}/usr/sbin/iodump

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf "$RPM_BUILD_ROOT"

%files
%defattr(-,root,root,-)
   /usr/sbin/iodump
   /usr/lib/iodump/kiodump.ko
   /usr/src/os_health/iodump/kiodump.conf

%pre
if [[ "%{current_kver}str" != $(uname -r)"str" ]];then
    echo "The current kernel version $(uname -r) is not supported by the current RPM package."
    exit 19
fi

%post
ps h -C iodump -o pid                        && killall iodump
[ -e /sys/module/kiodump/parameters/enable ] && echo N > /sys/module/kiodump/parameters/enable
lsmod | grep -qw kiodump                     && modprobe -r kiodump
if [ -e "/usr/lib/iodump/kiodump.ko" ];then
    install -d /lib/modules/%{current_kver}/extra/os_health/iodump/
    install /usr/lib/iodump/kiodump.ko /lib/modules/%{current_kver}/extra/os_health/iodump/kiodump.ko
    /sbin/depmod -aeF /boot/System.map-%{current_kver} %{current_kver} > /dev/null
    modprobe kiodump
    modprobe_ret=$?
    if [ $modprobe_ret -ne 0 ];then
        echo "kiodump.ko modprobe is failed, check the dmesg info."
        exit $modprobe_ret
    fi
else
    echo "The /usr/lib/iodump/kiodump.ko file does not exist in the iodump rpm package"
    exit 2
fi
if [ -d /etc/modules-load.d/ ];then
    install /usr/src/os_health/iodump/kiodump.conf /etc/modules-load.d/kiodump.conf
fi

%preun
if [ "$1" = "0" ]; then
    ps h -C iodump -o pid                        && killall iodump
    [ -e /sys/module/kiodump/parameters/enable ] && echo N > /sys/module/kiodump/parameters/enable
    lsmod | grep -qw kiodump                     && modprobe -r kiodump
    rm -f /lib/modules/%{current_kver}/extra/os_health/iodump/kiodump.ko
    /sbin/depmod -aeF /boot/System.map-%{current_kver} %{current_kver} > /dev/null
    rm -f /etc/modules-load.d/kiodump.conf
fi

%changelog
* Tue Mar 05 2024 wangxiaomeng <wangxiaomeng@kylinos.cn> - 1.0.1-6
- Fix crash when executing mkfs.xfs

* Mon Feb 05 2024 wangxiaomeng <wangxiaomeng@kylinos.cn> - 1.0.1-5
- Add debug_package

* Mon Feb 05 2024 wangxiaomeng <wangxiaomeng@kylinos.cn> - 1.0.1-4
- Fix crash when executing mkfs.xfs

* Mon Sep 25 2023 wangxiaomeng <wangxiaomeng@kylinos.cn> - 1.0.1-3
- Add BuildRequires: elfutils-devel

* Wed Sep 20 2023 wangxiaomeng <wangxiaomeng@kylinos.cn> - 1.0.1-2
- Fix compilation errors on x86 for kylin v10

* Wed Aug 24 2022 MilesWen <mileswen@linux.alibaba.com> - 1.0.1-1
- Release iodump RPM package
--end
