import os
import time

from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration

class CspiceConan(ConanFile):
    name = "cspice"
    description = "NASA C SPICE library"
    license = "TSPA"
    topics = ("conan", "spice", "naif", "kernels", "space", "nasa", "jpl", "spacecraft", "planet", "robotics")
    homepage = "https://naif.jpl.nasa.gov/naif/toolkit.html"
    url = "https://github.com/conan-io/conan-center-index"
    exports_sources = ["CMakeLists.txt", "patches/**"]
    exports = ["TSPA.txt"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    @property
    def _sources_idx_per_triplet(self):
        # Index of source code per triplet in conadata's "sources" field.
        return {
            "Macos": {
                "x86": {"apple-clang": 0},
                "x86_64": {"apple-clang": 1}
            },
            "Linux": {
                "x86": {"gcc": 2},
                "x86_64": {"gcc": 3}
            },
            "Windows": {
                "x86": {"Visual Studio": 4},
                "x86_64": {"Visual Studio": 5}
            },
            "cygwin": {
                "x86": {"gcc": 6},
                "x86_64": {"gcc": 7}
            },
            "SunOs": {
                "x86": {"sun-cc": 8},
                "x86_64": {"sun-cc": 9},
                "sparc": {"gcc": 10, "sun-cc": 11},
                "sparcv9": {"gcc": 12, "sun-cc": 13}
            }
        }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

        self._raise_if_not_supported_triplet()

    def _raise_if_not_supported_triplet(self):
        os = self._get_os_or_subsystem()
        arch = str(self.settings.arch)
        compiler = str(self.settings.compiler)
        if os not in self._sources_idx_per_triplet:
            raise ConanInvalidConfiguration("cspice does not support {0}".format(os))
        if arch not in self._sources_idx_per_triplet[os]:
            raise ConanInvalidConfiguration("cspice does not support {0} {1}".format(os, arch))
        if compiler not in self._sources_idx_per_triplet[os][arch]:
            raise ConanInvalidConfiguration("cspice does not support {0} on {1} {2}".format(compiler, os, arch))

    def _get_os_or_subsystem(self):
        if self.settings.os == "Windows" and self.settings.os.subsystem != "None":
            os_or_subsystem = str(self.settings.os.subsystem)
        else:
            os_or_subsystem = str(self.settings.os)
        return os_or_subsystem

    def source(self):
        pass

    def build(self):
        self._get_sources()
        os.rename(self.name, self._source_subfolder)
        for patch in self.conan_data["patches"][self.version]:
            tools.patch(**patch)
        cmake = self._configure_cmake()
        cmake.build()

    def _get_sources(self):
        os = self._get_os_or_subsystem()
        arch = str(self.settings.arch)
        compiler = str(self.settings.compiler)
        sources_idx = self._sources_idx_per_triplet[os][arch][compiler]
        tools.get(**self.conan_data["sources"][self.version][sources_idx])

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def package(self):
        self.copy("TSPA.txt", dst="licenses")
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.system_libs.append("m")
