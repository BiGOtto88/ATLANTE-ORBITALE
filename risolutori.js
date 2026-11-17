// RISOLUTORE A GRAFO PER 'ORBITE E MANOVRE'
// Utilizza la libreria math.js caricata nell'HTML

function calcolaOrbite() {
    let mu = parseFloat(document.getElementById('mu').value);
    let r1 = parseFloat(document.getElementById('r1').value);
    let r2 = parseFloat(document.getElementById('r2').value);
    let a = parseFloat(document.getElementById('a').value);
    let v = parseFloat(document.getElementById('v').value);
    
    let outputHtml = "<h3>Risultati Calcolati:</h3><ul>";
    let iteration = 0;
    let maxIterations = 5; 
    let newValuesFound = true;
    let computedSomething = false;

    // Motore di inferenza
    while (newValuesFound && iteration < maxIterations) {
        newValuesFound = false;

        // Da r e a, troviamo v
        if (!isNaN(mu) && !isNaN(r1) && !isNaN(a) && isNaN(v)) {
            v = math.sqrt(mu * (2/r1 - 1/a));
            outputHtml += `<li><strong>Velocità (v):</strong> ${v.toFixed(4)} km/s (Eq. vis viva)</li>`;
            document.getElementById('v').value = v;
            newValuesFound = true;
            computedSomething = true;
        }

        // Da r e v, troviamo a
        if (!isNaN(mu) && !isNaN(r1) && !isNaN(v) && isNaN(a)) {
            let energiaSpecifica = (Math.pow(v, 2) / 2) - (mu / r1);
            a = - mu / (2 * energiaSpecifica);
            outputHtml += `<li><strong>Semiasse maggiore (a):</strong> ${a.toFixed(2)} km</li>`;
            document.getElementById('a').value = a;
            newValuesFound = true;
            computedSomething = true;
        }

        // Trasferimento di Hohmann
        if (!isNaN(mu) && !isNaN(r1) && !isNaN(r2)) {
            if (!document.getElementById('delta_v_hohmann_calc') && iteration === 0) {
                let a_transfer = (r1 + r2) / 2;
                let v1_circ = math.sqrt(mu / r1);
                let v2_circ = math.sqrt(mu / r2);
                let v_perigeo_trans = math.sqrt(mu * (2/r1 - 1/a_transfer));
                let v_apogeo_trans = math.sqrt(mu * (2/r2 - 1/a_transfer));
                
                let deltaV1 = Math.abs(v_perigeo_trans - v1_circ);
                let deltaV2 = Math.abs(v2_circ - v_apogeo_trans);
                let deltaV_totale = deltaV1 + deltaV2;
                let tempo_volo = math.pi * math.sqrt(Math.pow(a_transfer, 3) / mu);

                outputHtml += `<li id="delta_v_hohmann_calc"><strong>Trasferimento Hohmann (r1 &rarr; r2):</strong>
                                <br>&Delta;V_1: ${deltaV1.toFixed(4)} km/s
                                <br>&Delta;V_2: ${deltaV2.toFixed(4)} km/s
                                <br>&Delta;V_Totale: ${deltaV_totale.toFixed(4)} km/s
                                <br>Tempo di volo (TOF): ${tempo_volo.toFixed(1)} s</li>`;
                computedSomething = true;
            }
        }
        iteration++;
    }

    outputHtml += "</ul>";
    
    let outputDiv = document.getElementById('orbite-output');
    if (!computedSomething) {
         outputDiv.innerHTML = "<strong>Dati insufficienti o nessuna nuova variabile calcolabile.</strong> Aggiungi altri dati.";
    } else {
         outputDiv.innerHTML = outputHtml;
    }
    outputDiv.style.display = 'block';
}

function pulisciOrbite() {
    document.getElementById('r1').value = '';
    document.getElementById('r2').value = '';
    document.getElementById('a').value = '';
    document.getElementById('v').value = '';
    let outputDiv = document.getElementById('orbite-output');
    outputDiv.innerHTML = '';
    outputDiv.style.display = 'none';
}
