import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * APIConsultas.java
 *
 * SDK en Java para consultar la API de Divisas de forma nativa en Android, Java
 * Desktop/Backend.
 * Solo utiliza librerías estándar de Java. Dado que no usamos librerías
 * externas de JSON
 * para mantenerlo 100% nativo y drop-in, hace un parseo manual seguro del JSON
 * esperado.
 */
public class APIConsultas {

    private static final String URL_DATOS_GITHUB = "https://LucielDOD.github.io/API-Divisas/datos.json";

    /**
     * Clase contenedora para devolver resultados estandarizados (simulando
     * diccionarios de python/js).
     */
    public static class RespuestaAPI {
        public String status;
        public String mensaje;
        public String fechaConsulta;

        // Exclusivos de pedir lista
        public int cantidad;
        public List<String> divisas;

        // Exclusivos de pedir conversion
        public String codigo;
        public BigDecimal valor;
        public String divisaBase;
        public String divisaObjetivo;
    }

    private static String getFechaLocal() {
        SimpleDateFormat sdf = new SimpleDateFormat("dd-MM-yyyy HH:mm:ss");
        return sdf.format(new Date()); // Toma por defecto el TimeZone de la máquina/dispositivo local
    }

    private static String fetchJsonData() throws Exception {
        URL url = new URL(URL_DATOS_GITHUB);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");

        if (conn.getResponseCode() != 200) {
            throw new RuntimeException("HTTP GET Request Failed with Error code : " + conn.getResponseCode());
        }

        Scanner scanner = new Scanner(new InputStreamReader(conn.getInputStream()));
        scanner.useDelimiter("\\A");
        String json = scanner.hasNext() ? scanner.next() : "";
        scanner.close();
        return json;
    }

    /**
     * Parsea de manera rústica el JSON específico que entrega la API para evitar
     * dependencias
     * externas como GSON o Jackson. Solo útil para este schema en particular.
     */
    private static Map<String, BigDecimal> extractValoresDesdeJson(String json) {
        Map<String, BigDecimal> mapa = new HashMap<>();

        // Agregar manualmente el USD ya que todos los datos son relativos al USD
        mapa.put("USD", new BigDecimal("1.0"));

        // Regex para buscar "codigo": "EUR-USD" y "valor_actual": 0.84
        Pattern pCodigo = Pattern.compile("\"codigo\"\\s*:\\s*\"([^\"]+)\"");
        Pattern pValor = Pattern.compile("\"valor_actual\"\\s*:\\s*([0-9.]+)");

        Matcher mCodigo = pCodigo.matcher(json);
        Matcher mValor = pValor.matcher(json);

        // Asumiendo que vienen en el mismo orden dentro del objeto
        while (mCodigo.find() && mValor.find()) {
            String codigoOriginal = mCodigo.group(1);
            String codigoLimpio = codigoOriginal.replace("-USD", "");
            String valorStr = mValor.group(1);

            try {
                BigDecimal valor = new BigDecimal(valorStr);
                mapa.put(codigoLimpio, valor);
            } catch (Exception e) {
                // Ignorar valor invalido
            }
        }

        return mapa;
    }

    public static RespuestaAPI solicitarDivisasDisponibles() {
        RespuestaAPI res = new RespuestaAPI();
        try {
            String json = fetchJsonData();
            Map<String, BigDecimal> mapa = extractValoresDesdeJson(json);

            List<String> codigos = new ArrayList<>(mapa.keySet());
            Collections.sort(codigos);

            res.status = "success";
            res.cantidad = codigos.size();
            res.divisas = codigos;
            res.fechaConsulta = getFechaLocal();

        } catch (Exception e) {
            res.status = "error";
            res.mensaje = "Error al obtener divisas: " + e.getMessage();
        }
        return res;
    }

    public static RespuestaAPI solicitarValorDivisa(String divisaBase, String divisaObjetivo) {
        RespuestaAPI res = new RespuestaAPI();
        divisaBase = divisaBase.toUpperCase();
        divisaObjetivo = divisaObjetivo.toUpperCase();

        try {
            String json = fetchJsonData();
            Map<String, BigDecimal> valoresEnUSD = extractValoresDesdeJson(json);

            if (!valoresEnUSD.containsKey(divisaBase)) {
                res.status = "error";
                res.mensaje = "La divisa base '" + divisaBase + "' no se encuentra.";
                return res;
            }
            if (!valoresEnUSD.containsKey(divisaObjetivo)) {
                res.status = "error";
                res.mensaje = "La divisa objetivo '" + divisaObjetivo + "' no se encuentra.";
                return res;
            }

            BigDecimal valBase = valoresEnUSD.get(divisaBase);
            BigDecimal valObj = valoresEnUSD.get(divisaObjetivo);

            // Calculation (Base/USD) / (Objetivo/USD) = Relacion Directa
            BigDecimal resultado = valBase.divide(valObj, 4, RoundingMode.HALF_UP);

            res.status = "success";
            res.codigo = divisaBase + "-" + divisaObjetivo;
            res.valor = resultado;
            res.divisaBase = divisaBase;
            res.divisaObjetivo = divisaObjetivo;
            res.fechaConsulta = getFechaLocal();

        } catch (Exception e) {
            res.status = "error";
            res.mensaje = "Error al calcular conversiones: " + e.getMessage();
        }
        return res;
    }

    // Método main solo de demostración (se puede eliminar por el cliente final)
    public static void main(String[] args) {
        RespuestaAPI resultado = solicitarValorDivisa("USD", "CLP");
        if (resultado.status.equals("success")) {
            System.out.println("1 " + resultado.divisaBase + " = " + resultado.valor + " " + resultado.divisaObjetivo);
            System.out.println("Fecha local consulta: " + resultado.fechaConsulta);
        } else {
            System.out.println("Error: " + resultado.mensaje);
        }
    }
}
