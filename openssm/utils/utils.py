from typing import Any
import functools
import inspect
from openssm.utils.logging import logger


class Utils:
    @staticmethod
    def canonicalize_user_input(user_input: Any) -> list[dict]:
        """
        Make sure user_input is in the form of a list of dicts,
        e.g., [{"role": "user", "content": "hello"}].
        """
        logger.debug("start: user_input: %s", user_input)

        if isinstance(user_input, list):
            # [{"role": "user", "content": "xxx"}, ...]
            results = []
            for item in user_input:
                if isinstance(item, dict) and "role" in item and "content" in item:
                    # {"role": "user", "content": "xxx"}
                    results.append(item)
                else:
                    # {"xxx": "yyy"} or any xxx
                    results.append({"role": "user", "content": str(item)})

            user_input = results

        elif isinstance(user_input, str):
            # "xxx"
            user_input = [{"role": "user", "content": user_input}]

        elif isinstance(user_input, dict):
            # {"role": "user", "content": "xxx"}
            user_input = [user_input]

        else:
            user_input = [{"role": "user", "content": str(user_input)}]

        logger.debug("end: user_input: %s", user_input)

        return user_input

    @staticmethod
    def canonicalize_query_response(response: Any) -> list[dict]:
        """
        Make sure response is in the form of a list of dicts,
        e.g., [{"role": "assistant", "content": "hello"}].
        """
        if not isinstance(response, list):
            response = [response]

        results = []
        for item in response:
            if isinstance(item, str):
                # "xxx"
                result_item = {"role": "assistant", "content": item}

            elif isinstance(item, dict):
                if "role" in item and "content" in item:
                    # {"role": "assistant", "content": "xxx"}
                    result_item = item

                elif "response" in item:
                    # {"response": "xxx"}
                    result_item = {"role": "assistant", "content": item["response"]}

                else:
                    # {"xxx": "yyy"}
                    result_item = {"role": "assistant", "content": str(item)}

            else:
                # Any xxx
                result_item = {"role": "assistant", "content": str(item)}

            results.append(result_item)
            return results

    @staticmethod
    def _old_do_canonicalize_user_input(param_name):
        """
        Decorator to canonicalize SSM user input.
        """
        def outer_decorator(func):
            def wrapper(*args, **kwargs):
                if param_name in kwargs:
                    kwargs[param_name] = Utils.canonicalize_user_input(kwargs[param_name])
                return func(*args, **kwargs)
            return wrapper
        return outer_decorator

    @staticmethod
    def do_canonicalize_user_input(param_name):
        """
        Decorator to canonicalize SSM user input.
        """
        def outer_decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Get the function signature
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if param_name not in param_names:
                    raise ValueError(f"Function does not have parameter named {param_name}")

                if param_name in kwargs:
                    # param_name is called as a keyword argument
                    kwargs[param_name] = Utils.canonicalize_user_input(kwargs[param_name])
                else:
                    # param_name is called as a positional argument
                    param_index = param_names.index(param_name)
                    args_list = list(args)
                    args_list[param_index] = Utils.canonicalize_user_input(args_list[param_index])
                    args = tuple(args_list)

                return func(*args, **kwargs)
            return wrapper
        return outer_decorator

    @staticmethod
    def do_canonicalize_query_response(func):
        """
        Decorator to canonicalize SSM query response.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)  # Execute the function first
            result = Utils.canonicalize_query_response(result)  # Modify the result
            return result
        return wrapper

    @staticmethod
    def do_canonicalize_user_input_and_query_response(param_name):
        def outer_decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                decorated_func = Utils.do_canonicalize_user_input(param_name)(func)
                final_func = Utils.do_canonicalize_query_response(decorated_func)
                return final_func(*args, **kwargs)
            return wrapper
        return outer_decorator