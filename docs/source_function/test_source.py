import save_source_function
import some_module

if __name__ == "__main__":
    source_functions = save_source_function.get_source_functions(some_module.test2)
    print(source_functions)
