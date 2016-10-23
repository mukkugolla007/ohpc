#----------------------------------------------------------------------------bh-
# This RPM .spec file is part of the OpenHPC project.
#
# It may have been modified from the default version supplied by the underlying
# release package (if available) in order to apply patches, perform customized
# build/install configurations, and supply additional files to support
# desired integration conventions.
#
#----------------------------------------------------------------------------eh-

#
# spec file for package superlu_dist
#
# Copyright (c) 2012 SUSE LINUX Products GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#

#-ohpc-header-comp-begin-----------------------------

%include %{_sourcedir}/OHPC_macros
%{!?PROJ_DELIM: %global PROJ_DELIM -ohpc}

# OpenHPC convention: the default assumes the gnu toolchain and openmpi
# MPI family; however, these can be overridden by specifing the
# compiler_family and mpi_family variables via rpmbuild or other
# mechanisms.

%{!?compiler_family: %global compiler_family gnu}
%{!?mpi_family:      %global mpi_family openmpi}

# Lmod dependency (note that lmod is pre-populated in the OpenHPC OBS build
# environment; if building outside, lmod remains a formal build dependency).
%if !0%{?OHPC_BUILD}
BuildRequires: lmod%{PROJ_DELIM}
%endif
# Compiler dependencies
BuildRequires: coreutils
%if %{compiler_family} == gnu
BuildRequires: gnu-compilers%{PROJ_DELIM}
Requires:      gnu-compilers%{PROJ_DELIM}
BuildRequires: scalapack-%{compiler_family}-%{mpi_family}%{PROJ_DELIM}
Requires:      scalapack-%{compiler_family}-%{mpi_family}%{PROJ_DELIM}
%endif
%if %{compiler_family} == intel
BuildRequires: gcc-c++ intel-compilers-devel%{PROJ_DELIM}
Requires:      gcc-c++ intel-compilers-devel%{PROJ_DELIM}
%if 0%{?OHPC_BUILD}
BuildRequires: intel_licenses
%endif
%endif

# MPI dependencies
%if %{mpi_family} == impi
BuildRequires: intel-mpi-devel%{PROJ_DELIM}
Requires:      intel-mpi-devel%{PROJ_DELIM}
%endif
%if %{mpi_family} == mvapich2
BuildRequires: mvapich2-%{compiler_family}%{PROJ_DELIM}
Requires:      mvapich2-%{compiler_family}%{PROJ_DELIM}
%endif
%if %{mpi_family} == openmpi
BuildRequires: openmpi-%{compiler_family}%{PROJ_DELIM}
Requires:      openmpi-%{compiler_family}%{PROJ_DELIM}
%endif
%if %{mpi_family} == mpich
BuildRequires: mpich-%{compiler_family}%{PROJ_DELIM}
Requires:      mpich-%{compiler_family}%{PROJ_DELIM}
%endif

#-ohpc-header-comp-end-------------------------------

# Base package name
%define pname superlu_dist
%define PNAME %(echo %{pname} | tr [a-z] [A-Z])

%define major   5
%define libname libsuperlu_dist

Name:           %{pname}-%{compiler_family}-%{mpi_family}%{PROJ_DELIM}
Version:        5.1.0
Release:        0
Summary:        A general purpose library for the direct solution of linear equations
License:        BSD-3-Clause
Group:          %{PROJ_NAME}/parallel-libs
URL:            http://crd-legacy.lbl.gov/~xiaoye/SuperLU/
Source0:        http://crd-legacy.lbl.gov/~xiaoye/SuperLU/superlu_dist_%{version}.tar.gz
Patch0:         superlu_dist-4.1-sequence-point.patch
Patch1:         superlu_dist-5.1-parmetis.patch
Patch2:         superlu_dist-5.1-cmake.patch
BuildRequires:  metis-%{compiler_family}%{PROJ_DELIM}
Requires:       metis-%{compiler_family}%{PROJ_DELIM}
BuildRequires:  cmake
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
DocDir:         %{OHPC_PUB}/doc/contrib

%include %{_sourcedir}/OHPC_macros
#!BuildIgnore: post-build-checks
%define debug_package %{nil}

# Default library install path
%define install_path %{OHPC_LIBS}/%{compiler_family}/%{mpi_family}/%{pname}/%version

%description
SuperLU is a general purpose library for the direct solution of large, sparse,
nonsymmetric systems of linear equations on high performance machines. The 
library is written in C and is callable from either C or Fortran. The library
routines will perform an LU decomposition with partial pivoting and triangular
system solves through forward and back substitution. The LU factorization routines
can handle non-square matrices but the triangular solves are performed only for
square matrices. The matrix columns may be preordered (before factorization)
either through library or user supplied routines. This preordering for sparsity 
is completely separate from the factorization. Working precision iterative
refinement subroutines are provided for improved backward stability. Routines
are also provided to equilibrate the system, estimate the condition number,
calculate the relative backward error, and estimate error bounds for the refined
solutions. 

%prep
%setup -q -n SuperLU_DIST_%{version}
%patch0 -p1
%patch1 -p1
%patch2 -p0

%build
# OpenHPC compiler/mpi designation
export OHPC_COMPILER_FAMILY=%{compiler_family}
export OHPC_MPI_FAMILY=%{mpi_family}
. %{_sourcedir}/OHPC_setup_compiler
. %{_sourcedir}/OHPC_setup_mpi

module load metis

%if %{compiler_family} == gnu
module load scalapack
%endif

cmake  \
     -DCMAKE_C_COMPILER=mpicc \
     -DCMAKE_C_FLAGS="-std=c99 -Wall -fPIC -DDEBUGlevel=0 -DPRNTlevel=0 -DPROFlevel=0" \
     -DCMAKE_Fortran_COMPILER=mpif90 \
     -DCMAKE_Fortran_FLAGS="-fPIC" \
     -Denable_parmetislib=OFF \
     -Denable_blaslib=ON \
     -DCMAKE_EXE_LINKER_FLAGS="-shared" \
     -DCMAKE_INSTALL_PREFIX=%{buildroot}%{install_path}

make install

mkdir tmp
(cd tmp; ar x %{buildroot}%{install_path}/lib/libsuperlu_dist.a)
mpif90 -z muldefs -shared -Wl,-soname=%{libname}.so.%{major} -o %{buildroot}%{install_path}/lib/%{libname}.so.%{version} tmp/*.o
pushd %{buildroot}%{install_path}/lib
ln -s %{libname}.so.%{version} %{libname}.so
popd


%install

%{__mkdir_p} %{buildroot}%{install_path}/etc
sed -i 's|%{buildroot}||g' make.inc
install -m644 make.inc %{buildroot}%{install_path}/etc

# OpenHPC module file
%{__mkdir_p} %{buildroot}%{OHPC_MODULEDEPS}/%{compiler_family}-%{mpi_family}/%{pname}
%{__cat} << EOF > %{buildroot}/%{OHPC_MODULEDEPS}/%{compiler_family}-%{mpi_family}/%{pname}/%{version}
#%Module1.0#####################################################################

proc ModulesHelp { } {

puts stderr " "
puts stderr "This module loads the SuperLU_dist library built with the %{compiler_family} compiler"
puts stderr "toolchain and the %{mpi_family} MPI stack."
puts stderr " "
puts stderr "Note that this build of SuperLU_dist leverages the metis library."
puts stderr "Consequently, this package is loaded automatically with this module."

puts stderr "\nVersion %{version}\n"

}
module-whatis "Name: %{pname} built with %{compiler_family} compiler and %{mpi_family} MPI"
module-whatis "Version: %{version}"
module-whatis "Category: runtime library"
module-whatis "Description: %{summary}"
module-whatis "%{url}"

set     version                     %{version}

# Require metis

if [ expr [ module-info mode load ] || [module-info mode display ] ] {
    if {  ![is-loaded metis]  } {
        module load metis
    }
}

prepend-path    PATH                %{install_path}/bin
prepend-path    INCLUDE             %{install_path}/include
prepend-path    LD_LIBRARY_PATH     %{install_path}/lib

setenv          %{PNAME}_DIR        %{install_path}
setenv          %{PNAME}_INC        %{install_path}/include
setenv          %{PNAME}_LIB        %{install_path}/lib

EOF

%{__cat} << EOF > %{buildroot}/%{OHPC_MODULEDEPS}/%{compiler_family}-%{mpi_family}/%{pname}/.version.%{version}
#%Module1.0#####################################################################
##
## version file for %{pname}-%{version}
##
set     ModulesVersion      "%{version}"
EOF

%{__mkdir_p} %{buildroot}/%_docdir

%clean
rm -rf %{buildroot}

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig


%files
%defattr(-,root,root,-)
%{OHPC_HOME}
%{OHPC_PUB}
%doc README

%changelog
