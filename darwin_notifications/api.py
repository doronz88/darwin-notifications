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

libobjc.objc_allocateClassPair.restype = ctypes.c_void_p
libobjc.objc_allocateClassPair.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]

libobjc.objc_registerClassPair.restype = None
libobjc.objc_registerClassPair.argtypes = [ctypes.c_void_p]

libobjc.class_addMethod.restype = ctypes.c_bool
libobjc.class_addMethod.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p]



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

_DELEGATE_INSTANCE = None
_SHOULD_PRESENT_IMP = None  # strong ref so GC doesn't free the IMP

def ensure_delegate(center_ptr: int):
    global _DELEGATE_INSTANCE, _SHOULD_PRESENT_IMP
    if _DELEGATE_INSTANCE:
        return

    NSObject = objc_getClass("NSObject")
    cls = libobjc.objc_allocateClassPair(NSObject, b"DNNotifyDelegate", 0)

    sig = b"c@:@@"  # BOOL, self, _cmd, center, notification

    should_present_proto = ctypes.CFUNCTYPE(
        ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
    )

    def _should_present(self, _cmd, _center, _notification):
        return True

    should_present = should_present_proto(_should_present)
    _SHOULD_PRESENT_IMP = should_present  # <-- keep strong ref

    libobjc.class_addMethod(
        cls,
        sel_registerName("userNotificationCenter:shouldPresentNotification:"),
        ctypes.cast(should_present, ctypes.c_void_p),
        sig,
    )
    libobjc.objc_registerClassPair(cls)

    alloc = create_objc_msgSend_t(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
    init  = create_objc_msgSend_t(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
    instance = init(alloc(cls, sel_registerName("alloc")), sel_registerName("init"))

    setDelegate = create_objc_msgSend_t(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
    setDelegate(center_ptr, sel_registerName("setDelegate:"), instance)

    _DELEGATE_INSTANCE = instance

CoreFoundation = ctypes.CDLL(ctypes.util.find_library("CoreFoundation"))
CoreFoundation.CFRunLoopRunInMode.restype = ctypes.c_int
CoreFoundation.CFRunLoopRunInMode.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_bool]
kCFRunLoopDefaultMode = ctypes.c_void_p.in_dll(CoreFoundation, "kCFRunLoopDefaultMode")

def pump_runloop(seconds: float = 0.3):
    CoreFoundation.CFRunLoopRunInMode(kCFRunLoopDefaultMode, seconds, False)


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

        # Give each notification a unique identifier to avoid coalescing
        set_obj(notif, sel_registerName("setIdentifier:"), ns_str(f"dn-{time.time_ns()}"))

        # [[NSUserNotificationCenter defaultUserNotificationCenter] deliverNotification:notif]
        NSUserNotificationCenter = objc_getClass("NSUserNotificationCenter")
        defaultCenter = create_objc_msgSend_t(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        )
        deliver = create_objc_msgSend_t(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        )

        center = defaultCenter(NSUserNotificationCenter, sel_registerName("defaultUserNotificationCenter"))

        # Ensure banner shows even if we're foreground
        ensure_delegate(center)

        deliver(center, sel_registerName("deliverNotification:"), notif)
        pump_runloop(1.5)  # instead of time.sleep


    finally:
        pool_drain(pool, sel_registerName("drain"))
