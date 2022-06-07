import netCDF4

def getVariableNames(path):
    f = netCDF4.Dataset(path)
    variables = f.variables.keys()
    return [v for v in list(variables) if len(f.variables[v]) > 24 ]
