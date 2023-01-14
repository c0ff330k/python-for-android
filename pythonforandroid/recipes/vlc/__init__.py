from pythonforandroid.toolchain import Recipe, current_directory
from pythonforandroid.logger import info, debug, shprint, warning
from os.path import join, isdir, isfile, dirname
from os import environ, listdir
import sh
import zipfile


class VlcRecipe(Recipe):
    version = '3.0.0'
    url = None
    name = 'vlc'

    depends = []
    specific_ndk = 'https://dl.google.com/android/repository/android-ndk-r21e-linux-x86_64.zip'
    port_git = 'https://github.com/videolan/vlc-android.git'
#    vlc_git = 'http://git.videolan.org/git/vlc.git'
    ENV_LIBVLC_AAR = 'LIBVLC_AAR'
    aars = {}  # for future use of multiple arch

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        port_dir = join(build_dir, 'vlc-port-android')
        if self.ENV_LIBVLC_AAR in environ:
            aar = environ.get(self.ENV_LIBVLC_AAR)
            if isdir(aar):
                aar = join(aar, 'libvlc-{}.aar'.format(self.version))
            if not isfile(aar):
                warning("Error: {} is not valid libvlc-<ver>.aar bundle".format(aar))
                info("check {} environment!".format(self.ENV_LIBVLC_AAR))
                exit(1)
            self.aars[arch] = aar
        else:
            aar_path = join(port_dir, 'libvlc', 'build', 'outputs', 'aar')
            self.aars[arch] = aar = join(aar_path, 'libvlc-{}.aar'.format(self.version))
            warning("HINT: set path to precompiled libvlc-<ver>.aar bundle "
                    "in {} environment!".format(self.ENV_LIBVLC_AAR))
            info("libvlc-<ver>.aar should build "
                 "from sources at {}".format(port_dir))
            if not isfile(join(port_dir, 'compile.sh')):
                info("clone vlc port for android sources from {}".format(
                            self.port_git))
                shprint(sh.git, 'clone', self.port_git, port_dir,
                        _tail=20, _critical=True)
# now "git clone ..." is a part of compile.sh
#            vlc_dir = join(port_dir, 'vlc')
#            if not isfile(join(vlc_dir, 'Makefile.am')):
#                info("clone vlc sources from {}".format(self.vlc_git))
#                shprint(sh.git, 'clone', self.vlc_git, vlc_dir,
#                            _tail=20, _critical=True)

    def build_arch(self, arch):
        super().build_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        port_dir = join(build_dir, 'vlc-port-android')
        aar = self.aars[arch]
        
        # install specific ndk
        ndks_dir = dirname(self.ctx.ndk_dir)
        ndk_name = ''
        if isdir(join(ndks_dir, 'vlc_ndk')):
            ndk_name = listdir(join(ndks_dir, 'vlc_ndk'))[0]
        else:
            shprint(sh.Command('wget'), '-O', join(ndks_dir, 'vlc_ndk.zip'), self.specific_ndk, _tail=50, _critical=True)
            with zipfile.ZipFile(join(ndks_dir, 'vlc_ndk.zip'), 'r') as zip_ref:
                ndk_name = zip_ref.namelist()[0]
                zip_ref.extractall(join(ndks_dir, 'vlc_ndk'))
        
        if not isfile(aar):
            with current_directory(port_dir):
                env = dict(environ)
                env.update({
                    'ANDROID_ABI': arch.arch,
                    'ANDROID_NDK': join(ndks_dir, 'vlc_ndk', ndk_name),
                    'ANDROID_SDK': self.ctx.sdk_dir,
                })
                info("compiling vlc from sources")
                debug("environment: {}".format(env))
                if not isfile(join('bin', 'VLC-debug.apk')):
                    shprint(sh.Command('./buildsystem/compile.sh'), '-a', 'armeabi-v7a', _env=env, _tail=50, _critical=True)
                shprint(sh.Command('./buildsystem/compile.sh'), '-l', '-a', 'armeabi-v7a', '-r', _env=env, _tail=50, _critical=True)
        shprint(sh.cp, '-a', aar, self.ctx.aars_dir)


recipe = VlcRecipe()
