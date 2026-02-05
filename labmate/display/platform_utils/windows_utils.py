"""This submodule contains functions that are specific for windows."""


def copy_fig(fig=None, format_=None, text_to_copy=None, **kwargs):  # pragma: no cover <--
    """Copy fig to the clipboard.

    Parameters
    ----------
    fig : matplotlib figure, optional
        If None, get the figure that has UI focus
    format : type of image to be pasted to the clipboard ('png', 'svg', 'jpg', 'jpeg')
        If None, uses matplotlib.rcParams["savefig.format"]
    text_to_copy: str to copy to the clipboard

    *args : arguments that are passed to savefig
    **kwargs : keywords arguments that are passed to savefig

    Raises
    ------
    ValueError
        If the desired format is not supported.

    AttributeError
        If no figure is found
    """
    # from win32gui import GetWindowText, GetForegroundWindow  # type: ignore import warnings
    from io import BytesIO

    import matplotlib.pyplot as plt
    import win32clipboard  # type: ignore import warnings

    # Determined available values by digging into windows API
    format_map = {
        "png": "PNG",
        "svg": "image/svg+xml",
        "jpg": "JFIF",
        "jpeg": "JFIF",
    }

    # If no format is passed to savefig get the default one
    if format_ is None:
        format_ = plt.rcParams["savefig.format"]
    format_ = format_.lower()

    if format_ not in format_map:
        format_ = "png"

    # if fig is None:
    #     # Find the figure window that has UI focus right now (not necessarily
    #     # the same as plt.gcf() when in interactive mode)
    #     fig_window_text = GetWindowText(GetForegroundWindow())
    #     for i in plt.get_fignums():
    #         if plt.figure(i).canvas.manager.get_window_title() == fig_window_text:  # type: ignore
    #             fig = plt.figure(i)
    #             break

    if fig is None:
        raise AttributeError("No figure found!")

    # Store the image in a buffer using savefig(). This has the
    # advantage of applying all the default savefig parameters
    # such as resolution and background color, which would be ignored
    # if we simply grab the canvas as displayed.
    with BytesIO() as buf:
        fig.savefig(buf, format=format_, **kwargs)

        if format_ != "svg":
            try:
                from PIL import Image

                im = Image.open(buf)
                with BytesIO() as output:
                    im.convert("RGB").save(output, "BMP")
                    data = output.getvalue()[14:]  # The file header off-set of BMP is 14 bytes
                    format_id = win32clipboard.CF_DIB  # DIB = device independent bitmap

            except ImportError:
                data = buf.getvalue()
                format_id = win32clipboard.RegisterClipboardFormat(format_map[format_])
        else:
            data = buf.getvalue()
            format_id = win32clipboard.RegisterClipboardFormat(format_map[format_])

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(format_id, data)
    if text_to_copy:
        win32clipboard.SetClipboardData(win32clipboard.CF_TEXT, text_to_copy.encode("utf-8"))

    win32clipboard.CloseClipboard()
