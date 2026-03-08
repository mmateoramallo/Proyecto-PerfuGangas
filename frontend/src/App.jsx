import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Package, TrendingUp, X, Filter } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

function App() {
  const [busqueda, setBusqueda] = useState(''); 
  const [perfumes, setPerfumes] = useState([]); 
  const [cargando, setCargando] = useState(false); 

  // --- NUEVOS ESTADOS PARA LOS FILTROS ---
  const [marcaFiltro, setMarcaFiltro] = useState('');
  const [ordenPrecio, setOrdenPrecio] = useState('');

  const [modalAbierto, setModalAbierto] = useState(false);
  const [perfumeSeleccionado, setPerfumeSeleccionado] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [cargandoHistorial, setCargandoHistorial] = useState(false);

  const buscarEnAPI = async (termino) => {
    setCargando(true);
    try {
      const respuesta = await axios.get(`http://127.0.0.1:8000/buscar?q=${termino}`);
      setPerfumes(respuesta.data); 
    } catch (error) {
      console.error("Error conectando con la API:", error);
    }
    setCargando(false);
  };

  useEffect(() => {
    buscarEnAPI(''); 
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
      const respuesta = await axios.get(`http://127.0.0.1:8000/historial/${perfume.id}`);
      setHistorial(respuesta.data);
    } catch (error) {
      console.error("Error trayendo el historial:", error);
    }
    setCargandoHistorial(false);
  };

  // ================= LÓGICA DE FILTROS Y ORDEN =================
  // 1. Obtenemos una lista limpia de las marcas disponibles
  const marcasUnicas = [...new Set(perfumes.map(p => p.marca))].sort();

  // 2. Aplicamos los filtros y el orden a los resultados antes de mostrarlos
  let perfumesProcesados = [...perfumes];

  if (marcaFiltro !== '') {
    perfumesProcesados = perfumesProcesados.filter(p => p.marca === marcaFiltro);
  }

  if (ordenPrecio === 'menor') {
    perfumesProcesados.sort((a, b) => (a.precio_actual || 0) - (b.precio_actual || 0));
  } else if (ordenPrecio === 'mayor') {
    perfumesProcesados.sort((a, b) => (b.precio_actual || 0) - (a.precio_actual || 0));
  }
  // =============================================================

  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans relative">
      
      <header className="bg-gray-950 border-b border-gray-800 py-6 px-4 sticky top-0 z-10 shadow-lg">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-red-500 flex items-center gap-2">
            <TrendingUp className="text-orange-500" />
            PerfuGangas
          </h1>
          <form onSubmit={manejarBusqueda} className="w-full md:w-1/2 relative group">
            <input
              type="text"
              placeholder="Buscar perfume, marca (Ej: Bleu, Dior)..."
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-full py-3 px-6 pl-12 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition-all"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
            <Search className="absolute left-4 top-3.5 text-gray-400 group-focus-within:text-orange-500 transition-colors" size={20} />
          </form>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-4 py-8">
        
        {/* ================= BARRA DE FILTROS ================= */}
        <div className="flex flex-col sm:flex-row justify-between items-center bg-gray-800/50 p-4 rounded-xl border border-gray-700 mb-8 gap-4">
          <div className="flex items-center gap-2 text-gray-400">
            <Filter size={20} className="text-orange-500"/>
            <span className="font-medium">Filtrar por:</span>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
            <select 
              className="bg-gray-900 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:border-orange-500 cursor-pointer"
              value={marcaFiltro}
              onChange={(e) => setMarcaFiltro(e.target.value)}
            >
              <option value="">Todas las Marcas</option>
              {marcasUnicas.map(marca => (
                <option key={marca} value={marca}>{marca}</option>
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
        {/* =================================================== */}

        {cargando ? (
          <div className="text-center text-orange-500 py-20 text-xl animate-pulse font-bold">
            Consultando la base de datos... 🚀
          </div>
        ) : (
          <>
            <p className="text-gray-400 mb-6 font-medium">
              Mostrando <span className="text-white font-bold">{perfumesProcesados.length}</span> resultados
            </p>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {/* ATENCIÓN: Ahora mapeamos "perfumesProcesados", no "perfumes" */}
              {perfumesProcesados.map((perfume) => (
                <div 
                  key={perfume.id} 
                  onClick={() => verDetalle(perfume)} 
                  className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700 hover:border-orange-500 hover:shadow-[0_0_20px_rgba(249,115,22,0.15)] hover:-translate-y-1 transition-all cursor-pointer group flex flex-col"
                >
                  <div className="h-48 bg-white flex items-center justify-center overflow-hidden border-b border-gray-700/50 relative">
                    {/* Etiqueta de precio sobre la foto */}
                    {perfume.precio_actual && (
                       <div className="absolute top-2 right-2 bg-gradient-to-r from-orange-600 to-red-600 text-white font-bold px-3 py-1 rounded-full text-sm shadow-lg z-10">
                         ${perfume.precio_actual.toLocaleString('es-AR')}
                       </div>
                    )}
                    
                    {perfume.imagen_url ? (
                      <img 
                        src={perfume.imagen_url} 
                        alt={perfume.nombre} 
                        className="h-full w-auto object-contain p-2 mix-blend-multiply transition-transform duration-300 group-hover:scale-110"
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
                      <h2 className="text-lg font-bold text-gray-100 leading-tight mb-3">
                        {perfume.nombre}
                      </h2>
                    </div>
                    <div>
                      <span className="inline-block bg-gray-700/50 border border-gray-600 text-gray-300 text-xs px-3 py-1 rounded-full font-medium">
                        {perfume.presentacion}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </main>

      {/* ================= MODAL DEL HISTORIAL ================= */}
      {modalAbierto && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
            
            <div className="flex justify-between items-center p-6 border-b border-gray-800">
              <div>
                <h3 className="text-2xl font-bold text-white">{perfumeSeleccionado?.nombre}</h3>
                <p className="text-orange-500 font-medium">{perfumeSeleccionado?.marca} - {perfumeSeleccionado?.presentacion}</p>
              </div>
              <button 
                onClick={() => setModalAbierto(false)}
                className="text-gray-400 hover:text-white bg-gray-800 hover:bg-red-500 p-2 rounded-full transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            <div className="p-6 h-96">
              {cargandoHistorial ? (
                <div className="h-full flex items-center justify-center text-orange-500 animate-pulse">
                  Cargando historial de precios...
                </div>
              ) : historial.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={historial} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="fecha" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" tickFormatter={(value) => `$${value}`} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#F3F4F6' }}
                      formatter={(value) => [`$${value}`, 'Precio']}
                      labelFormatter={(label) => `Fecha: ${label}`}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="precio" 
                      stroke="#F97316" 
                      strokeWidth={3}
                      activeDot={{ r: 8, fill: "#EF4444" }} 
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-400">
                  Aún no hay registros de precios para este perfume.
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