import React, { useState, useEffect } from "react";
import axios from "axios";
import { Search, Package, TrendingUp, X, Filter, Store, ChevronLeft, ChevronRight } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

function App() {
  const [busqueda, setBusqueda] = useState("");
  const [perfumes, setPerfumes] = useState([]);
  const [cargando, setCargando] = useState(false);

  const [marcaFiltro, setMarcaFiltro] = useState("");
  const [tiendaFiltro, setTiendaFiltro] = useState(""); 
  const [ordenPrecio, setOrdenPrecio] = useState("");

  // ESTADOS PARA PAGINACIÓN
  const [paginaActual, setPaginaActual] = useState(1);
  const itemsPorPagina = 20;

  const [modalAbierto, setModalAbierto] = useState(false);
  const [perfumeSeleccionado, setPerfumeSeleccionado] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [cargandoHistorial, setCargandoHistorial] = useState(false);

  const buscarEnAPI = async (termino) => {
    setCargando(true);
    try {
      const respuesta = await axios.get(
        `http://127.0.0.1:8000/buscar?q=${termino}`,
      );
      setPerfumes(respuesta.data);
      setPaginaActual(1); // Resetear a la página 1 cuando se hace una nueva búsqueda
    } catch (error) {
      console.error("Error conectando con la API:", error);
    }
    setCargando(false);
  };

  useEffect(() => {
    buscarEnAPI("");
  }, []);

  useEffect(() => {
    const temporizador = setTimeout(() => {
      buscarEnAPI(busqueda);
    }, 300);
    return () => clearTimeout(temporizador);
  }, [busqueda]);

  const manejarBusqueda = (e) => {
    e.preventDefault();
    buscarEnAPI(busqueda);
  };

  const verDetalle = async (perfume) => {
    setPerfumeSeleccionado(perfume);
    setModalAbierto(true);
    setCargandoHistorial(true);
    try {
      const respuesta = await axios.get(
        `http://127.0.0.1:8000/historial/${perfume.id}`,
      );
      setHistorial(respuesta.data);
    } catch (error) {
      console.error("Error trayendo el historial:", error);
    }
    setCargandoHistorial(false);
  };

  const marcasUnicas = [...new Set(perfumes.map((p) => p.marca))].sort();
  let perfumesProcesados = [...perfumes];

  if (marcaFiltro !== "") {
    perfumesProcesados = perfumesProcesados.filter(
      (p) => p.marca === marcaFiltro,
    );
  }

  if (tiendaFiltro !== "") {
    perfumesProcesados = perfumesProcesados.filter(
      (p) => p.tiendas && p.tiendas.includes(tiendaFiltro),
    );
  }

  if (ordenPrecio === "menor") {
    perfumesProcesados.sort(
      (a, b) => (a.precio_actual || 0) - (b.precio_actual || 0),
    );
  } else if (ordenPrecio === "mayor") {
    perfumesProcesados.sort(
      (a, b) => (b.precio_actual || 0) - (a.precio_actual || 0),
    );
  }

  // LÓGICA DE PAGINACIÓN
  // Al aplicar filtros, volvemos a la página 1
  useEffect(() => {
    setPaginaActual(1);
  }, [marcaFiltro, tiendaFiltro, ordenPrecio]);

  const indiceUltimoItem = paginaActual * itemsPorPagina;
  const indicePrimerItem = indiceUltimoItem - itemsPorPagina;
  const perfumesPaginados = perfumesProcesados.slice(indicePrimerItem, indiceUltimoItem);
  const totalPaginas = Math.ceil(perfumesProcesados.length / itemsPorPagina);

  const irPaginaSiguiente = () => {
    if (paginaActual < totalPaginas) setPaginaActual(paginaActual + 1);
  };

  const irPaginaAnterior = () => {
    if (paginaActual > 1) setPaginaActual(paginaActual - 1);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans relative">
      <header className="bg-gray-950 border-b border-gray-800 py-6 px-4 sticky top-0 z-20 shadow-lg">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-red-500 flex items-center gap-2 cursor-pointer" onClick={() => window.location.reload()}>
            <TrendingUp className="text-orange-500" />
            PerfuGangas
          </h1>
          <form
            onSubmit={manejarBusqueda}
            className="w-full md:w-1/2 relative group"
          >
            <input
              type="text"
              placeholder="Buscar perfume, marca (Ej: Bleu, Dior)..."
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-full py-3 px-6 pl-12 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition-all"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
            <Search
              className="absolute left-4 top-3.5 text-gray-400 group-focus-within:text-orange-500 transition-colors"
              size={20}
            />
          </form>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-4 py-8">
        <div className="flex flex-col sm:flex-row justify-between items-center bg-gray-800/50 p-4 rounded-xl border border-gray-700 mb-8 gap-4">
          <div className="flex items-center gap-2 text-gray-400">
            <Filter size={20} className="text-orange-500" />
            <span className="font-medium">Filtros:</span>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
            <div className="relative">
              <Store
                size={16}
                className="absolute left-3 top-3 text-gray-400"
              />
              <select
                className="bg-gray-900 border border-gray-600 text-white rounded-lg pl-9 pr-4 py-2 w-full focus:outline-none focus:border-orange-500 cursor-pointer appearance-none"
                value={tiendaFiltro}
                onChange={(e) => setTiendaFiltro(e.target.value)}
              >
                <option value="">Todas las Tiendas</option>
                <option value="Juleriaque">Juleriaque</option>
                <option value="Fiorani">Fiorani</option>
                <option value="Parfumerie">Parfumerie</option>
              </select>
            </div>

            <select
              className="bg-gray-900 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:border-orange-500 cursor-pointer"
              value={marcaFiltro}
              onChange={(e) => setMarcaFiltro(e.target.value)}
            >
              <option value="">Todas las Marcas</option>
              {marcasUnicas.map((marca) => (
                <option key={marca} value={marca}>
                  {marca}
                </option>
              ))}
            </select>

            <select
              className="bg-gray-900 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:border-orange-500 cursor-pointer"
              value={ordenPrecio}
              onChange={(e) => setOrdenPrecio(e.target.value)}
            >
              <option value="">Orden recomendado</option>
              <option value="menor">Precio: Menor a Mayor</option>
              <option value="mayor">Precio: Mayor a Menor</option>
            </select>
          </div>
        </div>

        {cargando ? (
          <div className="text-center text-orange-500 py-20 text-xl animate-pulse font-bold">
            Consultando la base de datos... 🚀
          </div>
        ) : (
          <>
            <p className="text-gray-400 mb-6 font-medium">
              Mostrando{" "}
              <span className="text-white font-bold">
                {perfumesProcesados.length}
              </span>{" "}
              resultados
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {perfumesPaginados.map((perfume) => (
                <div
                  key={perfume.id}
                  onClick={() => verDetalle(perfume)}
                  className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700 hover:border-orange-500 hover:shadow-[0_0_20px_rgba(249,115,22,0.15)] hover:-translate-y-1 transition-all cursor-pointer group flex flex-col relative z-0"
                >
                  {/* ARREGLO DEL BUG VISUAL: Contenedor relativo y z-index 0 para la imagen */}
                  <div className="h-56 bg-white flex items-center justify-center border-b border-gray-700/50 relative overflow-hidden">
                    {perfume.precio_actual && (
                      <div className="absolute top-3 right-3 bg-gradient-to-r from-orange-600 to-red-600 text-white font-bold px-3 py-1 rounded-full text-sm shadow-md z-10">
                        ${perfume.precio_actual.toLocaleString("es-AR")}
                      </div>
                    )}
                    {perfume.imagen_url ? (
                      <img
                        src={perfume.imagen_url}
                        alt={perfume.nombre}
                        className="h-full w-full object-contain p-4 mix-blend-multiply transition-transform duration-300 group-hover:scale-110"
                      />
                    ) : (
                      <Package size={64} className="text-gray-300" />
                    )}
                  </div>

                  <div className="p-5 flex-grow flex flex-col justify-between">
                    <div>
                      <p className="text-orange-500 text-xs font-bold uppercase tracking-wider mb-1">
                        {perfume.marca}
                      </p>
                      <h2 className="text-lg font-bold text-gray-100 leading-tight mb-3 line-clamp-2">
                        {perfume.nombre}
                      </h2>
                    </div>

                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className="inline-block bg-gray-700/50 border border-gray-600 text-gray-300 text-xs px-3 py-1 rounded-full font-medium">
                        {perfume.presentacion}
                      </span>

                      {perfume.tiendas &&
                        perfume.tiendas.split(" | ").map((tienda, idx) => (
                          <span
                            key={idx}
                            className="inline-block bg-blue-900/30 border border-blue-700 text-blue-300 text-xs px-3 py-1 rounded-full font-medium"
                          >
                            {tienda}
                          </span>
                        ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* CONTROLES DE PAGINACIÓN */}
            {totalPaginas > 1 && (
              <div className="mt-12 flex items-center justify-center gap-4">
                <button
                  onClick={irPaginaAnterior}
                  disabled={paginaActual === 1}
                  className={`p-2 rounded-full border ${
                    paginaActual === 1
                      ? "border-gray-700 text-gray-600 cursor-not-allowed"
                      : "border-orange-500 text-orange-500 hover:bg-orange-500 hover:text-white transition-colors"
                  }`}
                >
                  <ChevronLeft size={24} />
                </button>
                
                <span className="text-gray-300 font-medium">
                  Página <span className="text-white">{paginaActual}</span> de {totalPaginas}
                </span>

                <button
                  onClick={irPaginaSiguiente}
                  disabled={paginaActual === totalPaginas}
                  className={`p-2 rounded-full border ${
                    paginaActual === totalPaginas
                      ? "border-gray-700 text-gray-600 cursor-not-allowed"
                      : "border-orange-500 text-orange-500 hover:bg-orange-500 hover:text-white transition-colors"
                  }`}
                >
                  <ChevronRight size={24} />
                </button>
              </div>
            )}
          </>
        )}
      </main>

      {/* MODAL DEL HISTORIAL CON EFECTO BLUR */}
      {modalAbierto && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-4xl overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
            <div className="flex justify-between items-center p-6 border-b border-gray-800">
              <div>
                <h3 className="text-2xl font-bold text-white">
                  {perfumeSeleccionado?.nombre}
                </h3>
                <p className="text-orange-500 font-medium">
                  {perfumeSeleccionado?.marca} -{" "}
                  {perfumeSeleccionado?.presentacion}
                </p>
              </div>
              <button
                onClick={() => setModalAbierto(false)}
                className="text-gray-400 hover:text-white bg-gray-800 hover:bg-red-500 p-2 rounded-full transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            <div className="p-6 h-[400px]">
              {cargandoHistorial ? (
                <div className="h-full flex items-center justify-center text-orange-500 animate-pulse font-medium text-lg">
                  Dibujando historial de precios...
                </div>
              ) : historial.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={historial}
                    margin={{ top: 10, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="fecha" stroke="#9CA3AF" />
                    <YAxis
                      stroke="#9CA3AF"
                      tickFormatter={(value) => `$${value}`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1F2937",
                        borderColor: "#374151",
                        color: "#F3F4F6",
                        borderRadius: "0.5rem"
                      }}
                      formatter={(value, name) => [`$${value.toLocaleString("es-AR")}`, name]}
                      labelFormatter={(label) => `Fecha: ${label}`}
                    />
                    <Legend verticalAlign="top" height={36} />

                    <Line
                      type="monotone"
                      dataKey="precio_Juleriaque"
                      name="Juleriaque"
                      stroke="#F97316"
                      strokeWidth={3}
                      activeDot={{ r: 8, fill: "#F97316" }}
                      connectNulls={true}
                    />
                    <Line
                      type="monotone"
                      dataKey="precio_Fiorani"
                      name="Fiorani"
                      stroke="#10B981"
                      strokeWidth={3}
                      activeDot={{ r: 8, fill: "#10B981" }}
                      connectNulls={true}
                    />
                    <Line
                      type="monotone"
                      dataKey="precio_Parfumerie"
                      name="Parfumerie"
                      stroke="#8B5CF6"
                      strokeWidth={3}
                      activeDot={{ r: 8, fill: "#8B5CF6" }}
                      connectNulls={true}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
                  <TrendingUp size={48} className="text-gray-600 opacity-50" />
                  <p>Aún no hay registros históricos para este perfume.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;