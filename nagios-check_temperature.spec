%define _enable_debug_packages	%{nil}
%define debug_package		%{nil}

Summary:	A Nagios wrapper script around digitemp
Name:		nagios-check_temperature
Version:	1.1
Release:	8
License:	BSD-like
Group:		Networking/Other
URL:		https://www.hoppie.nl/tempsens/
Source0:	http://www.hoppie.nl/tempsens/check_temperature
Requires:	digitemp
Requires:	nagios-plugins
BuildArch:  noarch
BuildRoot:	%{_tmppath}/%{name}-%{version}

%description
check_temperature: Nagios wrapper script around digitemp. Used to monitor a
couple of 1-wire temperature sensors and to raise an alarm when one of them
reports a temperature outside a predefined band.

%prep
%setup -q -T -c

%build

%install
rm -rf %{buildroot}

install -d -m 755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/get_temperature << 'EOF'
#!/bin/bash
#
# get_temperature: polls the temperature sensor array and leaves the
# temperatures in a state file. Called by cron every 5 minutes.

TMPFILE="/tmp/temperature.XXXXXX"
STATEFILE="%{_localstatedir}/lib/temperature/current"
DIGITEMP="%{_bindir}/digitemp"
DIGICONF="%{_sysconfdir}/digitemp.conf"

# error check #1
if ! [ -f \$DIGITEMP ]; then
    echo "\$DIGITEMP does not exist."
    echo "please do \"ln -snf %{_bindir}/digitemp_DS9097 %{_bindir}/digitemp\""
    exit 1
fi

# error check #2
if ! [ -f \$DIGICONF ]; then
    echo "\$DIGICONF does not exist."
    echo "please do \"%{_bindir}/digitemp -i -c \$DIGICONF -s /dev/ttyS0\""
    exit 1
fi

# Abort after first script error.
set -e

# Get a unique temporary tamper-proof file name.
tmp=\$(mktemp \$TMPFILE)

# Create a full poll list of the temperature array. This takes up to
# 5 seconds per sensor, and therefore must be done to a (slowly growing)
# temporary file.
\$DIGITEMP -c \$DIGICONF -a -q > \$tmp
chmod 644 \$tmp

# 'Atomically' move the freshly created state file in place.
mv \$tmp \$STATEFILE
EOF
chmod +x %{buildroot}%{_bindir}/get_temperature

install -d -m 755 %{buildroot}%{_datadir}/nagios/plugins
install -m 755 %{SOURCE0} %{buildroot}%{_datadir}/nagios/plugins

install -d -m 755 %{buildroot}%{_sysconfdir}/nagios/plugins.d
cat > %{buildroot}%{_sysconfdir}/nagios/plugins.d/check_temperature.cfg <<'EOF'
define command {
        command_name	check_temperature
        command_line	%{_datadir}/nagios/plugins/check_temperature -s $ARG1$ -t $ARG2$ -w $ARG3$ -c $ARG4$
}
EOF

install -d -m 755 %{buildroot}%{_sysconfdir}/cron.d
cat > %{buildroot}%{_sysconfdir}/cron.d/%{name} <<'EOF'
# Poll the temperature sensor array every five minutes.
*/5 * * * * root %{_bindir}/get_temperature

# Append the last poll to the history file after each whole hour.
4 * * * * root cat %{_localstatedir}/lib/temperature/current >> /var/log/temperature.log
EOF

install -d -m 755 %{buildroot}%{_sysconfdir}/logrotate.d
cat > %{buildroot}%{_sysconfdir}/logrotate.d/%{name} <<'EOF'
/var/log/temperature.log {
    missingok
    monthly
    compress
}
EOF

install -d -m 755 %{buildroot}%{_localstatedir}/lib/temperature

%if %mdkversion < 200900
%post
/sbin/service nagios condrestart > /dev/null 2>/dev/null || :

%postun
/sbin/service nagios condrestart > /dev/null 2>/dev/null || :
%endif

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%config(noreplace) %{_sysconfdir}/nagios/plugins.d/check_temperature.cfg
%config(noreplace) %{_sysconfdir}/cron.d/%{name}
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%{_datadir}/nagios/plugins/check_temperature
%{_bindir}/get_temperature
%{_localstatedir}/lib/temperature


%changelog
* Sat Dec 11 2010 Oden Eriksson <oeriksson@mandriva.com> 1.1-7mdv2011.0
+ Revision: 620467
- the mass rebuild of 2010.0 packages

* Mon Sep 14 2009 Thierry Vignaud <tv@mandriva.org> 1.1-6mdv2010.0
+ Revision: 440229
- rebuild

* Mon Dec 15 2008 Guillaume Rousse <guillomovitch@mandriva.org> 1.1-5mdv2009.1
+ Revision: 314683
- now a noarch package
- use a herein document for configuration
- reply on filetrigger for reloading nagios

* Tue Jul 29 2008 Thierry Vignaud <tv@mandriva.org> 1.1-4mdv2009.0
+ Revision: 253541
- rebuild

  + Pixel <pixel@mandriva.com>
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

* Fri Dec 21 2007 Olivier Blin <oblin@mandriva.com> 1.1-2mdv2008.1
+ Revision: 136618
- restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Tue Apr 17 2007 Oden Eriksson <oeriksson@mandriva.com> 1.1-2mdv2008.0
+ Revision: 13797
- use the new /etc/nagios/plugins.d scandir


* Wed Nov 15 2006 Oden Eriksson <oeriksson@mandriva.com> 1.1-1mdv2007.0
+ Revision: 84579
- Import nagios-check_temperature

* Sun Sep 17 2006 Oden Eriksson <oeriksson@mandriva.com> 1.1-1mdv2007.0
- initial Mandriva package

