from . import pumps, loads, joints, assembly

def create_pump(params):
    flow = read_param_values(params, 'FlowRate', [0, 0])
    pres = read_param_values(params, 'PressureHead', [0, 0])
    speed = read_param_values(params, 'PumpSpeedPct', [0])[0]
    block = pumps.CentrifugalPump(flow, pres)
    block.set_speedPct(speed)
    return block

def create_resi(params):
    flow = read_param_values(params, 'FlowRate', [0, 0])
    pres = read_param_values(params, 'PressureDrop', [0, 0])
    block = loads.HydraulicResistance(flow, pres)
    return block

def create_valve(params):
    flow = read_param_values(params, 'FlowRate', [0, 0])
    pres = read_param_values(params, 'PressureDrop', [0, 0])
    pos = read_param_values(params, 'ValveOpeningPct', [0])[0]
    block = loads.HydraulicResistance(flow, pres)
    return block

def create_split(params):
    block = joints.TeeSplit()
    return block

def create_mixer(params):
    block = joints.TeeJoin()
    return block

def create_reservoir(params):
    pres = read_param_values(params, 'PressureConst', [0])[0]
    block = joints.HeaderTank(pres)
    return block

blockTypeDict = {
    'Pump': {'n_in': 1, 'n_out': 1, 'createFunc': create_pump},
    'Resistance' : {'n_in': 1, 'n_out': 1, 'createFunc': create_resi},
    'Valve': {'n_in': 1, 'n_out': 1, 'createFunc': create_valve},
    'Splitter': {'n_in': 1, 'n_out': 2, 'createFunc': create_split},
    'Mixer': {'n_in': 2, 'n_out': 1, 'createFunc': create_mixer},
    'Reservoir': {'n_in': 1, 'n_out': 1, 'createFunc': create_reservoir}
}

def create_block(blockType, params):
    if blockType not in blockTypeDict:
        raise Exception()
    return blockTypeDict[blockType]['createFunc'](params)

def read_param_values(params, key, default):
    try:
        text = params[key]
        text = text.replace('[', '')
        text = text.replace(']', '')
        text = text.replace(';', ',')
        textVals = text.split(',')
        textVals = [t for t in textVals if t != '']
        vals = list(map(float, textVals)) or default
    except Exception as e:
        print(f'Cannot read {key} parameter from the diagram data. Default value will be applied.')
        vals = default
    return vals

def read_connnection(blockType, conn):
    if blockType not in blockTypeDict:
        raise Exception()
    src = conn['from'].split('.')
    dst = conn['to'].split('.')
    uid1 = src[0]
    uid2 = dst[0]
    port1 = int(src[1].replace('Outlet', '')) - 1 + blockTypeDict[blockType]['n_in']
    port2 = int(dst[1].replace('Inlet', '')) - 1
    return uid1, uid2, port1, port2

def build_and_solve(diagramData):
    uids = []
    components = []
    connections = []
    for uid in diagramData:
        uids.append(uid)
        blockType = diagramData[uid]['type']

        params = diagramData[uid]['parameters']
        components.append(create_block(blockType, params))

        conns = diagramData[uid]['connections']
        for conn in conns:
            connections.append(read_connnection(blockType, conn))

    assy = assembly.HydraulicAssembly()
    for i, uid in enumerate(uids):
        assy.add_block(components[i], uid)
    for conn in connections:
        assy.connect_blocks(conn[0], conn[1], conn[2], conn[3])

    if not assy.blocks:
        raise Exception('There are no blocks in the diagram.')

    p0 = assy.get_avg_pressure()
    assy.set_init_pressure(p0)
    assy.solve()
    return get_port_states(assy)

def get_port_states(assy):
    states = {}
    for uid, block in assy.blocks.items():
        for i in range(block.n_out):
            portId = uid + '.Outlet' + str(i + 1)
            qId = block.ports[block.n_in + i].qId
            pId = block.ports[block.n_in + i].pId
            q = block.states[qId].value
            p = block.states[pId].value
            states[portId] = f'Q={q:.2f}, P={p:.2f}'
    return states

def run_solver(diagramData):
    status = 'fail'
    message = ''
    result = {}
    try:
        result = build_and_solve(diagramData)
        status = 'success'
    except Exception as e:
        message = str(e)
        print('Error in hydraulics model or solver: ' + message)

    return status, message, result
