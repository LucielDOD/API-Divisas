/**
 * API_consultas.js
 * 
 * SDK en JavaScript para consultar la API de Divisas de forma nativa en la web, Node.js y React Native.
 * No requiere instalación de librerías externas.
 * Utiliza fetch() nativo y resuelve promesas con el mismo formato que el SDK de Python.
 */

const URL_DATOS_GITHUB = "https://LucielDOD.github.io/API-Divisas/datos.json";

class APIConsultas {
    
    /**
     * Obtiene la lista de códigos de divisas disponibles leyendo el JSON remoto.
     * @returns {Promise<Object>} Promesa que resuelve a un objeto con el estado y las divisas.
     */
    static async solicitarDivisasDisponibles() {
        try {
            const response = await fetch(URL_DATOS_GITHUB);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            // Extraer códigos, removiendo el sufijo '-USD' y eliminando duplicados
            const codigosRudos = data.map(d => d.codigo.replace("-USD", ""));
            const codigosUnicos = [...new Set(codigosRudos)].sort();
            
            // Obtener fecha actual en la zona horaria del cliente local
            const fechaLocal = new Intl.DateTimeFormat('es-ES', { 
                dateStyle: 'short', 
                timeStyle: 'medium' 
            }).format(new Date());

            return {
                status: "success",
                cantidad: codigosUnicos.length,
                divisas: codigosUnicos,
                fecha_consulta: fechaLocal
            };
        } catch (error) {
            return {
                status: "error",
                mensaje: `Error al obtener divisas disponibles: ${error.message}`
            };
        }
    }

    /**
     * Calcula el valor de divisaBase expresado en divisaObjetivo extrayendo los datos remotamente.
     * @param {string} divisaBase - Ej. 'USD'
     * @param {string} divisaObjetivo - Ej. 'EUR'
     * @returns {Promise<Object>} Promesa con el resultado de la conversión.
     */
    static async solicitarValorDivisa(divisaBase, divisaObjetivo) {
        divisaBase = divisaBase.toUpperCase();
        divisaObjetivo = divisaObjetivo.toUpperCase();

        try {
            const response = await fetch(URL_DATOS_GITHUB);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            // Crear el mapa de valores respecto al USD
            const valoresEnUSD = {};
            data.forEach(d => {
                const codigoLimio = d.codigo.replace("-USD", "");
                valoresEnUSD[codigoLimio] = parseFloat(d.valor_actual);
            });
            
            if (!(divisaBase in valoresEnUSD)) {
                return { status: "error", mensaje: `La divisa base '${divisaBase}' no se encuentra en el origen de datos.` };
            }
            if (!(divisaObjetivo in valoresEnUSD)) {
                return { status: "error", mensaje: `La divisa objetivo '${divisaObjetivo}' no se encuentra en el origen de datos.` };
            }
            
            const valor1 = valoresEnUSD[divisaBase];
            const valor2 = valoresEnUSD[divisaObjetivo];
            
            // (Divisa 1 a USD) / (Divisa 2 a USD)
            const resultado = valor1 / valor2;
            
            // Obtener fecha actual local
            const fechaLocal = new Intl.DateTimeFormat('es-ES', { 
                dateStyle: 'short', 
                timeStyle: 'medium' 
            }).format(new Date());

            return {
                status: "success",
                codigo: `${divisaBase}-${divisaObjetivo}`,
                valor: Number(resultado.toFixed(4)),
                divisa_base: divisaBase,
                divisa_objetivo: divisaObjetivo,
                fecha_consulta: fechaLocal
            };

        } catch (error) {
            return {
                status: "error",
                mensaje: `Error al calcular divisas: ${error.message}`
            };
        }
    }
}

// Permitir importación en Node o como modulo en el navegador
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = APIConsultas;
} else {
    window.APIConsultas = APIConsultas;
}
