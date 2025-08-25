import ctypes
import ctypes.util
import time
from ctypes.util import find_library
from typing import Annotated

import typer

libobjc = ctypes.CDLL(find_library("libobjc.A.dylib"))
Foundation = ctypes.CDLL(find_library("Foundation"))

# Core runtime
libobjc.objc_getClass.restype = ctypes.c_void_p
libobjc.objc_getClass.argtypes = [ctypes.c_char_p]

libobjc.sel_registerName.restype = ctypes.c_void_p
libobjc.sel_registerName.argtypes = [ctypes.c_char_p]


def objc_getClass(name: str) -> ctypes.c_void_p:
    return libobjc.objc_getClass(name.encode("utf-8"))


def sel_registerName(name: str) -> ctypes.c_void_p:
    return libobjc.sel_registerName(name.encode("utf-8"))


def create_objc_msgSend_t(restype, *argtypes):
    """
    Return a typed callable for objc_msgSend that won't be mutated elsewhere.
    """
    return ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(restype, *argtypes))


NSString = objc_getClass("NSString")
stringWithUTF8String_ = create_objc_msgSend_t(
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p
)  # id stringWithUTF8String:(id, SEL, const char*)


def ns_str(py_str: str) -> ctypes.c_void_p:
    """Convert python string into NSString *"""
    return stringWithUTF8String_(NSString, sel_registerName("stringWithUTF8String:"), py_str.encode("utf-8"))


def notify(
        title: Annotated[
            str,
            typer.Option(
                "--title",
                "-t",
                help="The main title of the notification (required).",
            ),
        ],
        subtitle: Annotated[
            str,
            typer.Option(
                "--subtitle",
                "-s",
                help="Optional subtitle displayed under the title.",
            ),
        ] = "",
        text: Annotated[
            str,
            typer.Option(
                "--text",
                "-m",
                help="Informative message/body of the notification.",
            ),
        ] = "",
        sound: Annotated[
            bool,
            typer.Option(
                "--sound/--no-sound",
                help="Play the default notification sound.",
            ),
        ] = False) -> None:
    """Post NSUserNotification"""

    # @autoreleasepool
    NSAutoreleasePool = objc_getClass("NSAutoreleasePool")
    pool_new = create_objc_msgSend_t(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)  # +new
    pool_drain = create_objc_msgSend_t(None, ctypes.c_void_p, ctypes.c_void_p)  # -drain
    pool = pool_new(NSAutoreleasePool, sel_registerName("new"))

    try:
        # NSUserNotification *notif = [[NSUserNotification alloc] init]
        NSUserNotification = objc_getClass("NSUserNotification")
        alloc = create_objc_msgSend_t(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
        init = create_objc_msgSend_t(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)

        notif = alloc(NSUserNotification, sel_registerName("alloc"))
        notif = init(notif, sel_registerName("init"))

        set_obj = create_objc_msgSend_t(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)

        if title:
            set_obj(notif, sel_registerName("setTitle:"), ns_str(title))
        if subtitle:
            set_obj(notif, sel_registerName("setSubtitle:"), ns_str(subtitle))
        if text:
            set_obj(notif, sel_registerName("setInformativeText:"), ns_str(text))
        if sound:
            # NSString * const NSUserNotificationDefaultSoundName
            set_obj(notif, sel_registerName("setSoundName:"), ns_str("NSUserNotificationDefaultSoundName"))

        # [[NSUserNotificationCenter defaultUserNotificationCenter] deliverNotification:notif]
        NSUserNotificationCenter = objc_getClass("NSUserNotificationCenter")
        defaultCenter = create_objc_msgSend_t(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        )
        deliver = create_objc_msgSend_t(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        )

        center = defaultCenter(NSUserNotificationCenter, sel_registerName("defaultUserNotificationCenter"))
        deliver(center, sel_registerName("deliverNotification:"), notif)

        # Optional: keep process alive briefly so the banner can show if you exit immediately.
        # (Usually not needed, but harmless.)
        time.sleep(0.05)

    finally:
        pool_drain(pool, sel_registerName("drain"))
