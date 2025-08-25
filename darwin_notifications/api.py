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
    """Return a typed callable for objc_msgSend that won't be mutated elsewhere."""
    return ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(restype, *argtypes))


def objc_msgSend(obj: ctypes.c_void_p, selector: str, *args) -> ctypes.c_void_p:
    """Invoke `objc_msgSend`."""
    invocation = ctypes.cast(libobjc.objc_msgSend, ctypes.CFUNCTYPE(
        ctypes.c_void_p, *([ctypes.c_void_p] * (len(args) + 2))))
    return invocation(obj, sel_registerName(selector), *args)


NSString = objc_getClass("NSString")
NSAutoreleasePool = objc_getClass("NSAutoreleasePool")
NSUserNotification = objc_getClass("NSUserNotification")
NSUserNotificationCenter = objc_getClass("NSUserNotificationCenter")


def ns_str(py_str: str) -> ctypes.c_void_p:
    """Convert python string into NSString *"""
    return objc_msgSend(NSString, "stringWithUTF8String:", py_str.encode("utf-8"))


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
    # pool_new = create_objc_msgSend_t(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)  # +new
    # pool_drain = create_objc_msgSend_t(None, ctypes.c_void_p, ctypes.c_void_p)  # -drain
    pool = objc_msgSend(NSAutoreleasePool, "new")

    try:
        # NSUserNotification *notif = [NSUserNotification new]
        notif = objc_msgSend(NSUserNotification, "new")

        if title:
            objc_msgSend(notif, "setTitle:", ns_str(title))
        if subtitle:
            objc_msgSend(notif, "setSubtitle:", ns_str(subtitle))
        if text:
            objc_msgSend(notif, "setInformativeText:", ns_str(text))
        if sound:
            # NSString * const NSUserNotificationDefaultSoundName
            objc_msgSend(notif, "setSoundName:", ns_str("NSUserNotificationDefaultSoundName"))

        # [[NSUserNotificationCenter defaultUserNotificationCenter] deliverNotification:notif]
        center = objc_msgSend(NSUserNotificationCenter, "defaultUserNotificationCenter")
        objc_msgSend(center, "deliverNotification:", notif)

        # keep process alive briefly so the banner can show if you exit immediately.
        # (Usually not needed, but harmless.)
        time.sleep(0.05)

    finally:
        objc_msgSend(pool, "drain")
