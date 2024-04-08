# Advanced example

## Mode understanding

Modes can be set by providing `mode=..` keyword or explicitly by specifying `read_only` and `overwrite` options.

'w' mode is the same as

```python
>>> sd = DH5('somedata.h5', read_only=False)
```

'a' mode is the same as

```python
>>> sd = DH5('somedata.h5', read_only=False, overwrite=False)
```

'r' mode is the same as

```python
>>> sd = DH5('somedata.h5', read_only=True)
```

DH5.open_overwrite method is the same as

```python
>>> sd = DH5('somedata.h5', read_only=False, overwrite=True)
or
>>> sd = DH5('somedata.h5', mode='w', overwrite=True)
```
