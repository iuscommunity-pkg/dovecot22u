Summary: Dovecot Secure imap server
Name: dovecot
Version: 0.99.14
Release: 1.fc4
License: LGPL
Group: System Environment/Daemons

%define build_postgres 1
%define build_mysql 1

Source: %{name}-%{version}.tar.gz
Source1: dovecot.init
Source2: dovecot.pam
Source3: maildir-migration.txt
Source4: migrate-folders
Source5: migrate-users
Source6: perfect_maildir.pl
Source7: dovecot-REDHAT-FAQ.txt
Patch100: dovecot-conf.patch
Patch101: dovecot-configfile.patch
Patch102: dovecot-0.99-no-literal-plus-capability.patch
Patch103: dovecot-pam-setcred.patch

# Patches 500+ from upstream fixes
URL: http://dovecot.procontrol.fi/
Buildroot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires: openssl-devel
BuildRequires: openldap-devel
BuildRequires: pam-devel
BuildRequires: pkgconfig
BuildRequires: zlib-devel
# gettext-devel is needed for running autoconf because of the
# presence of AM_ICONV
BuildRequires: gettext-devel
Prereq: openssl, /sbin/chkconfig, /usr/sbin/useradd

%if %{build_postgres}
BuildRequires: postgresql-devel
%endif

%if %{build_mysql}
BuildRequires: mysql-devel
%endif

%define docdir %{_docdir}/%{name}-%{version}
%define ssldir /usr/share/ssl
%define restart_flag /tmp/%{name}-restart-after-rpm-install
%define dovecot_uid 97
%define dovecot_gid 97

%description
Dovecot is an IMAP server for Linux/UNIX-like systems, written with security 
primarily in mind.  It also contains a small POP3 server.  It supports mail 
in either of maildir or mbox formats.

%prep

%setup -q -n %{name}-%{version}

%patch100 -p1 -b .config
cp $RPM_BUILD_DIR/${RPM_PACKAGE_NAME}-${RPM_PACKAGE_VERSION}/dovecot-example.conf $RPM_BUILD_DIR/${RPM_PACKAGE_NAME}-${RPM_PACKAGE_VERSION}/dovecot.conf
%patch101 -p1 -b .configfile
%patch102 -p1 -b .no-literal-plus-capability
%patch103 -p1 -b .pam-setcred

%build
rm -f ./configure
aclocal
automake -a
autoconf
%configure                           \
	--with-docdir=%{docdir}	     \
%if %{build_postgres}
	--with-pgsql                 \
%endif
%if %{build_mysql}
	--with-mysql                 \
%endif
	--with-ssl=openssl           \
	--with-ssldir=%{ssldir}      \
	--with-ldap

make

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
rm -rf $RPM_BUILD_ROOT/%{_datadir}/%{name}
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rc.d/init.d
install -m 755 %{SOURCE1} $RPM_BUILD_ROOT/%{_sysconfdir}/rc.d/init.d/dovecot

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/pam.d
install -m 644 %{SOURCE2} $RPM_BUILD_ROOT/%{_sysconfdir}/pam.d/dovecot

# generate ghost .pem file
mkdir -p $RPM_BUILD_ROOT/%{ssldir}/{certs,private}
touch $RPM_BUILD_ROOT/%{ssldir}/{certs,private}/dovecot.pem
chmod 600 $RPM_BUILD_ROOT/%{ssldir}/{certs,private}/dovecot.pem

mkdir -p $RPM_BUILD_ROOT/var/run/dovecot
chmod 700 $RPM_BUILD_ROOT/var/run/dovecot
mkdir -p $RPM_BUILD_ROOT/var/run/dovecot-login

# Install some of our own documentation
install -m644 $RPM_SOURCE_DIR/dovecot-REDHAT-FAQ.txt $RPM_BUILD_ROOT%{docdir}/REDHAT-FAQ.txt

install -m755 -d $RPM_BUILD_ROOT%{docdir}/UW-to-Dovecot-Migration
for f in maildir-migration.txt migrate-folders migrate-users perfect_maildir.pl
do
    install -m644 $RPM_SOURCE_DIR/$f $RPM_BUILD_ROOT%{docdir}/UW-to-Dovecot-Migration
done

%pre
/usr/sbin/useradd -c "dovecot" -u %{dovecot_uid} -s /sbin/nologin -r -d /usr/libexec/dovecot dovecot 2>/dev/null || :

# stop service during installation, keep flag if it was running to restart later
rm -f %{restart_flag}
/sbin/service %{name} status >/dev/null 2>&1
if [ $? -eq 0 ]; then
    touch %{restart_flag}
    /sbin/service %{name} stop >/dev/null 2>&1
fi

%post
/sbin/chkconfig --add %{name}
# create a ssl cert
if [ ! -f %{ssldir}/certs/%{name}.pem ]; then
%{docdir}/examples/mkcert.sh &> /dev/null
fi
# Restart if it had been running before installation
if [ -e %{restart_flag} ]; then
  rm %{restart_flag}
  /sbin/service %{name} start >/dev/null 2>&1
fi
exit 0


%preun
if [ $1 = 0 ]; then
 /usr/sbin/userdel dovecot 2>/dev/null || :
 /usr/sbin/groupdel dovecot 2>/dev/null || :
 [ -f /var/lock/subsys/%{name} ] && /sbin/service %{name} stop > /dev/null 2>&1
 /sbin/chkconfig --del %{name}
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc %{docdir}
%config(noreplace) %{_sysconfdir}/dovecot.conf
%config %{_sysconfdir}/rc.d/init.d/dovecot
%config %{_sysconfdir}/pam.d/dovecot
%config(noreplace) %{ssldir}/dovecot-openssl.cnf
%attr(0600,root,root) %ghost %config(missingok,noreplace) %verify(not md5 size mtime) %{ssldir}/certs/dovecot.pem
%attr(0600,root,root) %ghost %config(missingok,noreplace) %verify(not md5 size mtime) %{ssldir}/private/dovecot.pem
%dir %{_libexecdir}/%{name}
%{_libexecdir}/%{name}/*
%{_sbindir}/dovecot
%dir /var/run/dovecot
%attr(0750,root,dovecot) %dir /var/run/dovecot-login
%attr(0750,root,dovecot) %{docdir}/examples/mkcert.sh


%changelog
* Mon Feb 14 2005 John Dennis <jdennis@redhat.com> - 0.99.14-1.fc4
- fix bug #147874, update to 0.99.14 release
  v0.99.14 2005-02-11  Timo Sirainen <tss at iki.fi>
  - Message address fields are now parsed differently, fixing some
    issues with spaces. Affects only clients which use FETCH ENVELOPE
    command.
  - Message MIME parser was somewhat broken with missing MIME boundaries
  - mbox: Don't allow X-UID headers in mails to override the UIDs we
    would otherwise set. Too large values can break some clients and
    cause other trouble.
  - passwd-file userdb wasn't working
  - PAM crashed with 64bit systems
  - non-SSL inetd startup wasn't working
  - If UID FETCH notices and skips an expunged message, don't return
    a NO reply. It's not needed and only makes clients give error
    messages.

* Wed Feb  2 2005 John Dennis <jdennis@redhat.com> - 0.99.13-4.devel
- fix bug #146198, clean up temp kerberos tickets

* Mon Jan 17 2005 John Dennis <jdennis@redhat.com> 0.99.13-3.devel
- fix bug #145214, force mbox_locks to fcntl only
- fix bug #145241, remove prereq on postgres and mysql, allow rpm auto
  dependency generator to pick up client lib dependency if needed.

* Thu Jan 13 2005 John Dennis <jdennis@redhat.com> 0.99.13-2.devel
- make postgres & mysql conditional build
- remove execute bit on migration example scripts so rpm does not pull
  in additional dependences on perl and perl modules that are not present
  in dovecot proper.
- add REDHAT-FAQ.txt to doc directory

* Thu Jan  6 2005 John Dennis <jdennis@redhat.com> 0.99.13-1.devel
- bring up to date with latest upstream, 0.99.13, bug #143707
  also fix bug #14462, bad dovecot-uid macro name

* Thu Jan  6 2005 John Dennis <jdennis@redhat.com> 0.99.11-10.devel
- fix bug #133618, removed LITERAL+ capability from capability string

* Wed Jan  5 2005 John Dennis <jdennis@redhat.com> 0.99.11-9.devel
- fix bug #134325, stop dovecot during installation

* Wed Jan  5 2005 John Dennis <jdennis@redhat.com> 0.99.11-8.devel
- fix bug #129539, dovecot starts too early,
  set chkconfig to 65 35 to match cyrus-imapd
- also delete some old commented out code from SSL certificate creation

* Thu Dec 23 2004 John Dennis <jdennis@redhat.com> 0.99.11-7.devel
- add UW to Dovecot migration documentation and scripts, bug #139954
  fix SSL documentation and scripts, add missing documentation, bug #139276

* Thu Nov 15 2004 Warren Togami <wtogami@redhat.com> 0.99.11-2.FC4.1
- rebuild against MySQL4

* Thu Oct 21 2004 John Dennis <jdennis@redhat.com>
- fix bug #136623
  Change License field from GPL to LGPL to reflect actual license

* Thu Sep 30 2004 John Dennis <jdennis@redhat.com> 0.99.11-1.FC3.3
- fix bug #124786, listen to ipv6 as well as ipv4

* Wed Sep  8 2004 John Dennis <jdennis@redhat.com> 0.99.11-1.FC3.1
- bring up to latest upstream,
  comments from Timo Sirainen <tss at iki.fi> on release v0.99.11 2004-09-04  
  + 127.* and ::1 IP addresses are treated as secured with
    disable_plaintext_auth = yes
  + auth_debug setting for extra authentication debugging
  + Some documentation and error message updates
  + Create PID file in /var/run/dovecot/master.pid
  + home setting is now optional in static userdb
  + Added mail setting to static userdb
  - After APPENDing to selected mailbox Dovecot didn't always notice the
    new mail immediately which broke some clients
  - THREAD and SORT commands crashed with some mails
  - If APPENDed mail ended with CR character, Dovecot aborted the saving
  - Output streams sometimes sent data duplicated and lost part of it.
    This could have caused various strange problems, but looks like in
    practise it rarely caused real problems.

* Wed Aug  4 2004 John Dennis <jdennis@redhat.com>
- change release field separator from comma to dot, bump build number

* Mon Aug  2 2004 John Dennis <jdennis@redhat.com> 0.99.10.9-1,FC3,1
- bring up to date with latest upstream, fixes include:
- LDAP support compiles now with Solaris LDAP library
- IMAP BODY and BODYSTRUCTURE replies were wrong for MIME parts which
  didn't contain Content-Type header.
- MySQL and PostgreSQL auth didn't reconnect if connection was lost
  to SQL server
- Linking fixes for dovecot-auth with some systems
- Last fix for disconnecting client when downloading mail longer than
  30 seconds actually made it never disconnect client. Now it works
  properly: disconnect when client hasn't read _any_ data for 30
  seconds.
- MySQL compiling got broken in last release
- More PostgreSQL reconnection fixing


* Mon Jul 26 2004 John Dennis <jdennis@redhat.com> 0.99.10.7-1,FC3,1
- enable postgres and mySQL in build
- fix configure to look for mysql in alternate locations
- nuke configure script in tar file, recreate from configure.in using autoconf

- bring up to latest upstream, which included:
- Added outlook-pop3-no-nuls workaround to fix Outlook hang in mails with NULs.
- Config file lines can now contain quoted strings ("value ")
- If client didn't finish downloading a single mail in 30 seconds,
  Dovecot closed the connection. This was supposed to work so that
  if client hasn't read data at all in 30 seconds, it's disconnected.
- Maildir: LIST now doesn't skip symlinks


* Wed Jun 30 2004 John Dennis <jdennis@redhat.com>
- bump rev for build
- change rev for FC3 build

* Fri Jun 25 2004 John Dennis <jdennis@redhat.com> - 0.99.10.6-1
- bring up to date with upstream,
  recent change log comments from Timo Sirainen were:
  SHA1 password support using OpenSSL crypto library
  mail_extra_groups setting
  maildir_stat_dirs setting
  Added NAMESPACE capability and command
  Autocreate missing maildirs (instead of crashing)
  Fixed occational crash in maildir synchronization
  Fixed occational assertion crash in ioloop.c
  Fixed FreeBSD compiling issue
  Fixed issues with 64bit Solaris binary

* Tue Jun 15 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Thu May 27 2004 David Woodhouse <dwmw2@redhat.com> 0.99.10.5-1
- Update to 0.99.10.5 to fix maildir segfaults (#123022)

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
