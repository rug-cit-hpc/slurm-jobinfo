Name: jobinfo
Version: 1.3.1
Release: 2%{?dist}
Summary: Collect job information from SLURM in nicely readable format.

Group: System Environment/Base
License: MIT
URL: https://github.com/rug-cit-ris/slurm-jobinfo
Source0: %{name}-%{version}.tar.gz
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Requires: python python-requests

%description
jobinfo - collates job information from the 'sstat', 'sacct' and 'squeue' SLURM commands to give a uniform interface for both current and historical jobs.

%prep
%setup -q

%build
#make

%install
mkdir -p $RPM_BUILD_ROOT/usr/bin
mkdir -p $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages
install jobinfo $RPM_BUILD_ROOT/usr/bin/jobinfo
install pynumparser.py $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages

%files
%defattr(-,root,root)
#%doc README
/usr/bin/jobinfo
/usr/lib/python2.7/site-packages/pynumparser.py*

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Mon Mar 23 2020 Bob Dröge <b.e.droge@rug.nl> - 1.3.1
- Bugfix: pynumparser could not be found when another Python version was loaded as module.

* Wed Mar 18 2020 Bob Dröge <b.e.droge@rug.nl> - 1.3.0
- Fix bug: do not attempt to parse Unknown as date for waiting jobs

* Mon Mar 16 2020 Bob Dröge <b.e.droge@rug.nl> - 1.2
- Support for multiple GPUs, implemented by Egon Rijpkema
- Stick to Python2 for now (default in CentOS 6)

* Tue Mar 10 2020 Bob Dröge <b.e.droge@rug.nl> - 1.1
- Added GPU usage reporting functionality, implemented by Egon Rijpkema

* Mon May 27 2019 Bob Dröge <b.e.droge@rug.nl> - 1.0
- Updated spec file, proper version number

* Tue Dec 13 2016 Bob Dröge <b.e.droge@rug.nl> - 13dec2016
- Python 3 compatibility
- Job efficiency percentage at CPU time

* Mon Mar 21 2016 Bob Dröge <b.e.droge@rug.nl> - 8dec2015
- Initial build
