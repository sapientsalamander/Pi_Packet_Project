#include <stdlib.h>
#include "python2.7/Python.h"

#define PYTHON_FILE_NAME "receive.py"

void *
initialize(void *unused)
{
    Py_SetProgramName(PYTHON_FILE_NAME);
    Py_Initialize();
    FILE *file;
    file = fopen(PYTHON_FILE_NAME, "r");
    PyRun_SimpleFile(file, PYTHON_FILE_NAME);
}

void *
finalize(void *unused)
{
    Py_Finalize();
}

int
print_lcd(const char *file, const char *function, const char *msg)
{
    setenv("PYTHONPATH", ".", 1);
    PyObject *pName, *pModule, *pDict, *pFunc;
    PyObject *pArgs, *pValue;
    int i;

    Py_Initialize();
    pName = PyString_FromString(file);
    /* Error checking of pName left out */

    pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule != NULL) {
        pFunc = PyObject_GetAttrString(pModule, function);
        /* pFunc is a new reference */

        if (pFunc && PyCallable_Check(pFunc)) {
            pArgs = PyTuple_New(1);
            for (i = 0; i < 1; ++i) {
                pValue = PyString_FromString(msg);
                if (!pValue) {
                    Py_DECREF(pArgs);
                    Py_DECREF(pModule);
                    fprintf(stderr, "Cannot convert argument\n");
                    return 1;
                }
                /* pValue reference stolen here: */
                PyTuple_SetItem(pArgs, i, pValue);
            }
            pValue = PyObject_CallObject(pFunc, pArgs);
            Py_DECREF(pArgs);
            /*if (pValue != NULL) {
                printf("Result of call: %ld\n", PyString_FromString(pValue));
                Py_DECREF(pValue);
            } else {
                Py_DECREF(pFunc);
                Py_DECREF(pModule);
                PyErr_Print();
                fprintf(stderr,"Call failed\n");
                return 1;
            }*/
        } else {
            if (PyErr_Occurred())
                PyErr_Print();
            fprintf(stderr, "Cannot find function \"%s\"\n", function);
        }
        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
    } else {
        PyErr_Print();
        fprintf(stderr, "Failed to load \"%s\"\n", file);
        return 1;
    }
    Py_Finalize();
    return 0;
}
