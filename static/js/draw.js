document.addEventListener("DOMContentLoaded", function () {
    const jsPlumbInstance = jsPlumb.getInstance({
        Container: "canvas",
    });

    const componentTypes = {
        "Pump": {
            parameters: [
                {label: "Flow Rate, lpm",       id: "FlowRate",     fallback: "0, 1"},
                {label: "Pressure Head, kPa",   id: "PressureHead", fallback: "0, 0"},
                {label: "Pump Speed, %",        id: "PumpSpeedPct", fallback: "100"}
            ],
            inlets: 1,
            outlets: 1
        },
        "Resistance": {
            parameters: [
                {label: "Flow Rate, lpm",       id: "FlowRate",     fallback: "0, 1"},
                {label: "Pressure Drop, kPa",   id: "PressureDrop", fallback: "0, 0"}
            ],
            inlets: 1,
            outlets: 1
        },
        "Valve": {
            parameters: [
                {label: "Flow Rate, lpm",       id: "FlowRate",     fallback: "0, 0"},
                {label: "Pressure Drop, kPa",   id: "PressureDrop", fallback: "0, 1"},
                {label: "Valve Opening, %",     id: "ValveOpeningPct", fallback: "100"}
            ],
            inlets: 1,
            outlets: 1
        },
        "Pipe": {
            parameters: [
                {label: "Inner Diameter, m",    id: "InnerDiameter", fallback: "1"},
                {label: "Pipe Length, m",       id: "PipeLength", fallback: "0"}
            ],
            inlets: 1,
            outlets: 1
        },
        "Splitter": {
            parameters: [],
            inlets: 1,
            outlets: 2
        },
        "Mixer": {
            parameters: [],
            inlets: 2,
            outlets: 1
        },
        "Reservoir": {
            parameters: [
                {label: "Absolute Pressure, kPa", id: "PressureConst", fallback: "0"},
            ],
            inlets: 1,
            outlets: 1
        }
    };

    const connectorPaintStyle = {
            stroke: "black",
            strokeWidth: 1,
            joinstyle: "round",
            outlineStroke: "white",
            outlineWidth: 1
        },
        endpointHoverStyle = {
            fill: "#216477",
            stroke: "#216477"
        },
        connectorHoverStyle = {
            stroke: "#216477",
            strokeWidth: 2,
            outlineStroke: "white",
            outlineWidth: 1
        },
        sourceEndPoint = {
            anchor: "RightMiddle",
            isSource: true,
            endpoint: "Dot",
            connector: ["Flowchart",  { gap: 5, cornerRadius: 5 }],
            connectorStyle: connectorPaintStyle,
            paintStyle: { fill: "lightgrey", radius: 5, outlineStroke: "black", outlineWidth: 1 },
            hoverPaintStyle: endpointHoverStyle,
            connectorHoverStyle: connectorHoverStyle
        },
        targetEndPoint = {
            anchor: "LeftMiddle",
            isTarget: true,
            dropOptions: { hoverClass: "hover", activeClass: "active" },
            endpoint: "Dot",
            paintStyle: { fill: "lightblue", radius: 5, outlineStroke: "black", outlineWidth: 1 },
        }

    let componentCounter = 0;
    const components = {};
    const results = [];

    document.getElementById("addComponent").addEventListener("click", function () {
        const componentType = document.getElementById("componentType").value;
        addComponent(componentType);
    });

    function addComponent(type) {
        componentCounter++;
        const id = type + componentCounter;
        const component = document.createElement("div");
        component.classList.add("component");
        component.id = id;

        component.innerHTML = `<div style='padding: 5px'><img src='/static/img/${type}.png' alt='${type}'/>`
        component.innerHTML += `<div class='label'>${id}</div>`;
        if (componentTypes[type].parameters.length > 0){
            component.innerHTML += `<button class='button-edit' id='${id}.editComponent'>Edit</button>`;
        }
        component.innerHTML += `<button class='button-del' id='${id}.delComponent'>Del</button></div>`;

        const inlets = [];
        const outlets = [];
        const n_in = componentTypes[type].inlets;
        const n_out = componentTypes[type].outlets;
        let pos = 0;
        let portId = ''
        for (let i = 0; i < n_in; i++) {
            pos += 100. / (n_in+1);
            portId = `${id}.Inlet${i+1}`;
            inlets.push(portId);
            component.innerHTML += `<div class='inlet' style='top: ${pos}%;' id='${portId}'></div>`;
        }
        pos = 0;
        for (let i = 0; i < n_out; i++) {
            pos += 100. / (n_out+1);
            portId = `${id}.Outlet${i+1}`;
            outlets.push(portId);
            component.innerHTML += `<div class='outlet' style='top: ${pos}%;' id='${portId}'></div>`;
        }

        document.getElementById("canvas").appendChild(component);

        if (componentTypes[type].parameters.length > 0){
            document.getElementById(`${id}.editComponent`).addEventListener("click", function () {
                editComponent(id, type);
            });
        }
        document.getElementById(`${id}.delComponent`).addEventListener("click", function (){
            delComponent(id);
        });

        jsPlumbInstance.draggable(component, { containment: "parent" });

        // Make the OUTLET port a SOURCE
        outlets.forEach(outlet => jsPlumbInstance.addEndpoint(outlet, sourceEndPoint));
        // Make the INLET port a TARGET
        inlets.forEach(inlet => jsPlumbInstance.addEndpoint(inlet, targetEndPoint));

        paramDefaults = {};
        componentTypes[type].parameters.forEach(param => {
            paramDefaults[param.id] = param.fallback;
        });
        components[id] = { type: type, parameters: paramDefaults, connections: [] };
    }

    function editComponent(id, type) {
        const component = document.getElementById(id);
        let editDiv = document.getElementById("editForm");
        if (editDiv) {
            editDiv.remove();
            if (id == editDiv.parentId){
                return;
            }
        }

        editDiv = document.createElement("div");
        editDiv.id = "editForm";
        editDiv.parentId = id;
        editDiv.classList.add('form-box')

        const rect = component.getBoundingClientRect();
        editDiv.style.left = rect.width + 10 + "px";
        editDiv.style.top = "0px";

        const predefinedParams = componentTypes[type].parameters;
        let formHTML = "Enter parameters:<div class='form-params'>";
        predefinedParams.forEach(param => {
            const currentValue = components[id].parameters[param.id] || '';
            formHTML += `<label for='${param.id}'>${param.label}</label>`;
            formHTML += `<input style='min-width: 0;' type='text' id='${param.id}' value='${currentValue}'/>`;
        });
        formHTML += `</div><button id='${id}.saveParameters'>Save</button>`;
        editDiv.innerHTML = formHTML;

        component.appendChild(editDiv);
        document.getElementById(`${id}.saveParameters`).addEventListener("click", function () {
            saveParameters(id, predefinedParams);
        });
    }

    function saveParameters(id, predefinedParams) {
        predefinedParams.forEach(param => {
            const inputElement = document.getElementById(`${param.id}`);
            if (inputElement) {
                components[id].parameters[param.id] = inputElement.value;
            }
        });
        document.getElementById("editForm").remove();
        removeOutletOverlays();
    }

    function delComponent(id) {
        const editDiv = document.getElementById("editForm");
        if (editDiv && id == editDiv.parentId){
            editDiv.remove();
        }
        jsPlumbInstance.remove(id);
        delete components[id];
        removeOutletOverlays();
    }

    document.getElementById("solve").addEventListener("click", function () {
        updateConnections();

        fetch("/solve", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken(),
            },
            body: JSON.stringify(components),
        })
//        .then(() => {window.location.href = "/solve";});
        .then(response => response.json())
        .then(data => displayResults(data))
        .catch(error => {
            let data = { 'status': 'error', 'message': 'Solver is not responding.'};
            displayResults(data);
            console.error('Error:', error);
        });

        let xml = '<diagram>\n';
        for (let id in components) {
            let comp = components[id];
            const params = Object.entries(comp.parameters).map(([k, v]) => `<param name='${k}' value='${v}'/>`).join('\n');
            const connections = comp.connections.map(conn => `<connection from='${conn.from}' to='${conn.to}'/>`).join('\n');
            xml += `<component id='${id}' type='${comp.type}'>\n`
            if (params.length > 0){
                xml += params + "\n";
            }
            if (connections.length > 0){
                xml += connections + '\n';
            }
            xml += '</component>\n';
        }
        xml += '</diagram>';
        console.log(xml);
    });

    function updateConnections() {
        const connections = jsPlumbInstance.getAllConnections();
        console.log(connections)
        for (let id in components) {
            components[id].connections = [];
        }
        connections.forEach(conn => {
            const src = document.getElementById(conn.sourceId).parentElement.id;
            components[src].connections.push({from: conn.sourceId, to: conn.targetId});
        });
    }

    function displayResults(data) {
        console.log(data);
        if (data.status == 'success') {
            showPopup('✅ Done!', 'green');
            addOutletOverlays(data.result);
        }
        else if (data.status == 'marginal') {
            showPopup('⚠️ Solution Not Converged!\nReview parameters and connections.', 'darkorange');
            addOutletOverlays(data.result);
        }
        else {
            showPopup('❌ Calculation Failed!\n' + data.message, 'darkred');
            removeOutletOverlays();
        }
    }

    function addOutletOverlays(result) {
        for (let portId in result) {
            const port = document.getElementById(portId);
            if (!port) continue;

            const overlayId = `${portId}.Data`;
            let overlay = document.getElementById(overlayId);
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = overlayId;
                overlay.classList.add('outlet-overlay');
                port.appendChild(overlay);
            }
            overlay.innerHTML = result[portId];
            results.push(overlay);
        }
    }

    function removeOutletOverlays() {
        while (results.length > 0){
            res = results.pop();
            res.remove();
        }
    }

    function showPopup(message, color) {
        let popup = document.getElementById('msgPopup');
        if (popup) {
            popup.remove();
        }
        popup = document.createElement('div');
        popup.id = 'msgPopup';
        popup.innerText = message;
        popup.style.backgroundColor = color
        popup.classList.add('msg-popup')
        document.body.appendChild(popup);
        setTimeout(() => { document.body.removeChild(popup); }, 5000);
    }

    function getCSRFToken() {
        const name = 'csrftoken=';
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name)) {
                return cookie.substring(name.length);
            }
        }
        return '';
    }
});
