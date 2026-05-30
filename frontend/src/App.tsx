import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Playground from './pages/Playground';
import Warehouse from './pages/Warehouse';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Playground />} />
        <Route path="/warehouse" element={<Warehouse />} />
      </Routes>
    </Router>
  );
}
