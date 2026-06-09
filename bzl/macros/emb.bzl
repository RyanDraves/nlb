"""Common rules for embedded development"""

load("@rules_cc//cc:defs.bzl", "cc_library")
load("//bzl/macros:python.bzl", "py_binary", "py_test")

def flash(name, binary, **kwargs):
    """Flash a binary to a device

    Args:
        name: The name of the binary
        binary: The binary to flash
        **kwargs: Additional arguments to pass to `py_binary`
    """
    py_binary(
        name = name,
        srcs = ["//emb/project/base:flash.py"],
        # Does not play nice with platforms
        add_completions = False,
        main = "//emb/project/base:flash.py",
        deps = [
            "//emb/project/base:flash",
        ],
        data = [binary],
        args = [
            "$(location {0})".format(binary),
        ],
        **kwargs
    )

def wav_cc_library(
        name,
        wav,
        symbol,
        sample_rate = 22050,
        namespace = "emb::yaal::clips",
        gain_db = 0.0,
        pad_ms = 50,
        visibility = None,
        **kwargs):
    """Embed a WAV file as a C++ `emb::yaal::AudioClip` library

    Args:
        name: The name of the library
        wav: The WAV file to embed
        symbol: The name of the generated `AudioClip` symbol
        sample_rate: The target sample rate, in Hz
        namespace: The C++ namespace for the generated symbol
        gain_db: Gain to apply to the samples, in dB
        pad_ms: Zero-padding appended to the clip, in milliseconds
        visibility: The visibility of the library
        **kwargs: Additional arguments to pass to `cc_library`
    """
    hpp = name + ".hpp"
    cc = name + ".cc"

    cmd = ("$(execpath //nlb/wav:wav2cc) -i $(location {wav})" +
           " --output-hpp $(RULEDIR)/{hpp} --output-cc $(RULEDIR)/{cc}" +
           " --header-include {pkg}/{hpp} --symbol {symbol}" +
           " --namespace {namespace} --sample-rate {sample_rate}" +
           " --gain-db {gain_db} --pad-ms {pad_ms}").format(
        wav = wav,
        hpp = hpp,
        cc = cc,
        pkg = native.package_name(),
        symbol = symbol,
        namespace = namespace,
        sample_rate = sample_rate,
        gain_db = gain_db,
        pad_ms = pad_ms,
    )

    native.genrule(
        name = name + "_gen",
        srcs = [wav],
        outs = [hpp, cc],
        cmd = cmd,
        tools = ["//nlb/wav:wav2cc"],
    )

    cc_library(
        name = name,
        srcs = [cc],
        hdrs = [hpp],
        visibility = visibility,
        deps = ["//emb/yaal:audio_clip"],
        **kwargs
    )

def host_test(name, srcs, binary, deps, **kwargs):
    """Run a host test

    Args:
        name: The name of the binary
        srcs: The source files for the test
        binary: The binary to run
        deps: The dependencies for the test
        **kwargs: Additional arguments to pass to `py_binary`
    """
    py_test(
        name = name,
        srcs = srcs,
        deps = deps,
        data = [binary],
        env = {
            "HOST_BIN": "$(rootpath {0})".format(binary),
        },
        **kwargs
    )
