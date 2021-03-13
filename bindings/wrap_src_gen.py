import xml.etree.ElementTree as et
import os
import sys

script_path = os.path.dirname(os.path.realpath(__file__))
typesystem_file = os.path.join(script_path, "bindings.xml")

def get_cpp_files_gen(args):
    ts_tree = et.parse(typesystem_file)
    ts_root = ts_tree.getroot()

    package_name = ts_root.attrib['package']
    
    type_tags = ['object-type', 'value-type']
    types = [child.attrib['name'] for child in ts_root if child.tag in type_tags]
    cpp_files_gen = [f'{package_name.lower()}_module_wrapper.cpp']
    cpp_files_gen.extend([f'{typename.lower()}_wrapper.cpp' for typename in types])
    

    if len(args) > 0:
        cpp_files_gen = [os.path.join(package_name, f) for f in cpp_files_gen]
        cpp_files_gen = [os.path.join(args[1], f) for f in cpp_files_gen]
    
    return cpp_files_gen

def cmake(args):
    files = get_cpp_files_gen(args)
    if sys.platform == "win32":
        files = map(lambda x: x.replace("\\", "/"), files)
    sys.stdout.write(";".join(files))    

if len(sys.argv) < 2:
    print('Usage: [base path]')
    exit(1)

cmake(sys.argv)