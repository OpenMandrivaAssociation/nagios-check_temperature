%define _enable_debug_packages	%{nil}
%define debug_package		%{nil}

Summary:	A Nagios wrapper script around digitemp
Name:		nagios-check_temperature
Version:	1.1
Release:	%mkrel 1
License:	BSD-like
Group:		Networking/Other
URL:		http://www.hoppie.nl/tempsens/
Source0:	http://www.hoppie.nl/tempsens/check_temperature.bz2
Source1:	checkcommands.cfg.bz2
Source2:	services.cfg.bz2
Requires:	digitemp
Requires:	nagios
BuildRoot:	%{_tmppath}/%{name}-buildroot

%description
check_temperature: Nagios wrapper script around digitemp. Used to monitor a
couple of 1-wire temperature sensors and to raise an alarm when one of them
reports a temperature outside a predefined band.

%prep

%setup -q -T -c

bzcat %{SOURCE0} > check_temperature
bzcat %{SOURCE1} > checkcommands.cfg
bzcat %{SOURCE2} > services.cfg

# lib64 fix
perl -pi -e "s|/usr/lib\b|%{_libdir}|g" *

%build

cat > get_temperature << EOF
#!/bin/bash
#
# get_temperature: polls the temperature sensor array and leaves the
# temperatures in a state file. Called by cron every 5 minutes.

TMPFILE="/tmp/temperature.XXXXXX"
STATEFILE="%{_localstatedir}/temperature/current"
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

cat > %{name}.crond << EOF
# Poll the temperature sensor array every five minutes.
*/5 * * * * root %{_bindir}/get_temperature

# Append the last poll to the history file after each whole hour.
4 * * * * root cat %{_localstatedir}/temperature/current >> /var/log/temperature.log
EOF

cat > %{name}.logrotate << EOF
/var/log/temperature.log {
    missingok
    monthly
    compress
}
EOF

%install
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

install -d %{buildroot}%{_sysconfdir}/cron.d
install -d %{buildroot}%{_sysconfdir}/logrotate.d
install -d %{buildroot}%{_libdir}/nagios/plugins
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_localstatedir}/temperature

install -m0755 check_temperature %{buildroot}%{_libdir}/nagios/plugins/
install -m0755 get_temperature %{buildroot}%{_bindir}/
install -m0644 %{name}.crond %{buildroot}%{_sysconfdir}/cron.d/%{name}
install -m0644 %{name}.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc checkcommands.cfg services.cfg
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/cron.d/%{name}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%attr(0755,root,root) %{_libdir}/nagios/plugins/check_temperature
%attr(0755,root,root) %{_bindir}/get_temperature
%dir %attr(0755,root,root) %{_localstatedir}/temperature


