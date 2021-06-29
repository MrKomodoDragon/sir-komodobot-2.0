import asyncio
import functools
from typing import Callable, TypeVar
from typing_extensions import ParamSpec
P = ParamSpec("P")
R = TypeVar("R")
Fn = Callable[P, R]
def to_thread(func: Fn[P, R]):
	@functools.wraps(func)
	async def wrapper(*args: P.args, **kwargs: P.kwargs):
		return await asyncio.to_thread(func, *args, **kwargs)
	return wrapper
