# Installing a Julia Kernel Into Jupyter Notebook
After updating to a newer release of Julia (`juliaup update`), any installed kernels for use with Jupyter notebooks will kindly invalidate themselves.

[IJulia](https://julialang.github.io/IJulia.jl/stable/manual/installation/) provides the correct instructions for re-installing a Julia kernel. Running in the Julia interpreter _outside a VsCode terminal_:
```Julia
using IJulia
installkernel("Julia nodeps", "--depwarn=no")
```
