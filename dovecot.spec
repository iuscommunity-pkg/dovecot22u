Summary: Dovecot Secure imap server
Name: dovecot
Version: 0.99.10.4
Release: 4
License: GPL
Group: System Environment/Daemons
Source: %{name}-%{version}.tar.gz
Source1: dovecot.init
Source2: dovecot.pam
Patch100: dovecot-0.99.10.4-conf.patch

# Patches 500+ from upstream fixes
Patch500: dovecot-0.99.10.4-maildir.patch
Patch501: dovecot-0.99.10.4-customflags-fix.patch
Patch502: dovecot-0.99.10.4-imap-fetch-body-section.patch
URL: http://dovecot.procontrol.fi/
Buildroot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires: openssl-devel
BuildRequires: openldap-devel
BuildRequires: pam-devel
BuildRequires: pkgconfig
BuildRequires: zlib-devel
Prereq: openssl, /sbin/chkconfig, /usr/sbin/useradd

%description
Dovecot is an IMAP server for Linux/UNIX-like systems, written with security 
primarily in mind.  It also contains a small POP3 server.  It supports mail 
in either of maildir or mbox formats.

%prep

%setup -q -n %{name}-%{version}

%patch100 -p1 -b .config

%patch500 -p0 -b .maildir
%patch501 -p0 -b .customflags-fix
%patch502 -p1 -b .imap-fetch-body-section

%build
%configure --with-ssl=openssl --with-ssldir=/usr/share/ssl --with-ldap

make

%install
rm -rf $RPM_BUILD_ROOT
%makeinstall
rm -rf $RPM_BUILD_ROOT/%{_datadir}/%{name}
install -m 644 dovecot-example.conf $RPM_BUILD_ROOT/%{_sysconfdir}/dovecot.conf
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rc.d/init.d
install -m 755 %{SOURCE1} $RPM_BUILD_ROOT/%{_sysconfdir}/rc.d/init.d/dovecot

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/pam.d
install -m 644 %{SOURCE2} $RPM_BUILD_ROOT/%{_sysconfdir}/pam.d/dovecot

# generate ghost .pem file
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/ssl/{certs,private}
touch $RPM_BUILD_ROOT/%{_datadir}/ssl/{certs,private}/dovecot.pem
chmod 600 $RPM_BUILD_ROOT/%{_datadir}/ssl/{certs,private}/dovecot.pem

mkdir -p $RPM_BUILD_ROOT/var/run/dovecot
chmod 700 $RPM_BUILD_ROOT/var/run/dovecot
mkdir -p $RPM_BUILD_ROOT/var/run/dovecot-login

# the dovecot make install installs docs.  blah.
rm -rf $RPM_BUILD_ROOT/%{_docdir}/%{name}
rm -f $RPM_BUILD_ROOT/etc/dovecot-example.conf

%pre
/usr/sbin/useradd -c "dovecot" -u 97 -s /sbin/nologin -r -d /usr/libexec/dovecot dovecot 2>/dev/null || :

%post
/sbin/chkconfig --add dovecot
# create a ssl cert
if [ ! -f %{_datadir}/ssl/certs/dovecot.pem ]; then
pushd %{_datadir}/ssl &>/dev/null
umask 077
cat << EOF | openssl req -new -x509 -days 365 -nodes -out certs/dovecot.pem -keyout private/dovecot.pem &>/dev/null
--
SomeState
SomeCity
SomeOrganization
SomeOrganizationalUnit
localhost.localdomain
root@localhost.localdomain
EOF
chown root:root private/dovecot.pem certs/dovecot.pem
chmod 600 private/dovecot.pem certs/dovecot.pem
popd &>/dev/null
fi
exit 0


%preun
if [ $1 = 0 ]; then
 /usr/sbin/userdel dovecot 2>/dev/null || :
 /usr/sbin/groupdel dovecot 2>/dev/null || :
 [ -f /var/lock/subsys/dovecot ] && /sbin/service dovecot stop > /dev/null 2>&1
 /sbin/chkconfig --del dovecot
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc doc/*.txt doc/dovecot-openssl.cnf doc/mkcert.sh INSTALL AUTHORS ChangeLog COPYING TODO README NEWS COPYING.LGPL
%config(noreplace) %{_sysconfdir}/dovecot.conf
%config %{_sysconfdir}/rc.d/init.d/dovecot
%config %{_sysconfdir}/pam.d/dovecot
%attr(0600,root,root) %ghost %config(missingok,noreplace) %verify(not md5 size mtime) %{_datadir}/ssl/certs/dovecot.pem
%attr(0600,root,root) %ghost %config(missingok,noreplace) %verify(not md5 size mtime) %{_datadir}/ssl/private/dovecot.pem
%dir %{_libexecdir}/%{name}
%{_libexecdir}/%{name}/*
%{_sbindir}/dovecot
%dir /var/run/dovecot
%attr(0750,root,dovecot) %dir /var/run/dovecot-login


%changelog
* Fri May 07 2004 Warren Togami <wtogami@redhat.com> 0.99.10.4-4
- default auth config that is actually usable
- Timo Sirainen (author) suggested functionality fixes
  maildir, imap-fetch-body-section, customflags-fix

* Mon Feb 23 2004 Tim Waugh <twaugh@redhat.com>
- Use ':' instead of '.' as separator for chown.

* Tue Feb 17 2004 Jeremy Katz <katzj@redhat.com> - 0.99.10.4-3
- restart properly if it dies (#115594)

* Fri Feb 13 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Mon Nov 24 2003 Jeremy Katz <katzj@redhat.com> 0.99.10.4-1
- update to 0.99.10.4

* Mon Oct  6 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-7
- another patch from upstream to fix returning invalid data on partial 
  BODY[part] fetches
- patch to avoid confusion of draft/deleted in indexes

* Tue Sep 23 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-6
- add some patches from upstream (#104288)

* Thu Sep  4 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-5
- fix startup with 2.6 with patch from upstream (#103801)

* Tue Sep  2 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-4
- fix assert in search code (#103383)

* Tue Jul 22 2003 Nalin Dahyabhai <nalin@redhat.com> 0.99.10-3
- rebuild

* Thu Jul 17 2003 Bill Nottingham <notting@redhat.com> 0.99.10-2
- don't run by default

* Thu Jun 26 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-1
- 0.99.10

* Mon Jun 23 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-0.2
- 0.99.10-rc2 (includes ssl detection fix)
- a few tweaks from fedora
  - noreplace the config file
  - configure --with-ldap to get LDAP enabled

* Mon Jun 23 2003 Jeremy Katz <katzj@redhat.com> 0.99.10-0.1
- 0.99.10-rc1
- add fix for ssl detection
- add zlib-devel to BuildRequires
- change pam service name to dovecot
- include pam config

* Thu May  8 2003 Jeremy Katz <katzj@redhat.com> 0.99.9.1-1
- update to 0.99.9.1
- add patch from upstream to fix potential bug when fetching with 
  CR+LF linefeeds
- tweak some things in the initscript and config file noticed by the 
  fedora folks

* Sun Mar 16 2003 Jeremy Katz <katzj@redhat.com> 0.99.8.1-2
- fix ssl dir
- own /var/run/dovecot/login with the correct perms
- fix chmod/chown in post

* Fri Mar 14 2003 Jeremy Katz <katzj@redhat.com> 0.99.8.1-1
- update to 0.99.8.1

* Tue Mar 11 2003 Jeremy Katz <katzj@redhat.com> 0.99.8-2
- add a patch to fix quoting problem from CVS

* Mon Mar 10 2003 Jeremy Katz <katzj@redhat.com> 0.99.8-1
- 0.99.8
- add some buildrequires
- fixup to build with openssl 0.9.7
- now includes a pop3 daemon (off by default)
- clean up description and %%preun
- add dovecot user (uid/gid of 97)
- add some buildrequires
- move the ssl cert to %{_datadir}/ssl/certs
- create a dummy ssl cert in %post
- own /var/run/dovecot
- make the config file a source so we get default mbox locks of fcntl

* Sun Dec  1 2002 Seth Vidal <skvidal@phy.duke.edu>
- 0.99.4 and fix startup so it starts imap-master not vsftpd :)

* Tue Nov 26 2002 Seth Vidal <skvidal@phy.duke.edu>
- first build
