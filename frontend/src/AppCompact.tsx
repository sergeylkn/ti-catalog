import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Box,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress,
  Tabs,
  Tab,
  Slider,
  Paper,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import SendIcon from '@mui/icons-material/Send';
import TuneIcon from '@mui/icons-material/Tune';
import ChatIcon from '@mui/icons-material/Chat';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

interface ProductItem {
  id: string;
  title: string;
  sku?: string;
  description?: string;
  specs: Record<string, string>;
  category: string;
  pressure_bar?: number;
  diameter_mm?: number;
  material?: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

function TabPanel(props: any) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function App() {
  const [tabValue, setTabValue] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState<string[]>([]);
  const [searchResults, setSearchResults] = useState<ProductItem[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<ProductItem | null>(null);
  const [recommendations, setRecommendations] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [pressureRange, setPressureRange] = useState<[number, number]>([0, 100]);
  const [diameterRange, setDiameterRange] = useState<[number, number]>([0, 100]);
  const [selectedMaterial, setSelectedMaterial] = useState('');
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadCategories();
    loadStats();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const loadCategories = async () => {
    try {
      const res = await axios.get(`${API_BASE}/categories`);
      setCategories(res.data);
    } catch (err) {
      console.error('Error:', err);
    }
  };

  const loadStats = async () => {
    try {
      const res = await axios.get(`${API_BASE}/stats`);
      setStats(res.data);
    } catch (err) {
      console.error('Error:', err);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/search`, {
        query: searchQuery,
        category: selectedCategory || undefined,
        limit: 20,
      });
      setSearchResults(res.data.items);
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/filter`, {
        category: selectedCategory || undefined,
        pressure_min: pressureRange[0],
        pressure_max: pressureRange[1],
        diameter_min: diameterRange[0],
        diameter_max: diameterRange[1],
        material: selectedMaterial || undefined,
      });
      setSearchResults(res.data.items);
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleProductSelect = async (product: ProductItem) => {
    setSelectedProduct(product);
    try {
      const res = await axios.get(`${API_BASE}/recommendations/${product.id}`);
      setRecommendations(res.data);
    } catch (err) {
      console.error('Error:', err);
    }
  };

  const handleChatSend = async () => {
    if (!chatInput.trim()) return;
    const msg = chatInput;
    setChatMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/chat`, {
        session_id: sessionId,
        message: msg,
      });
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: res.data.assistant_response },
      ]);
    } catch (err) {
      setChatMessages((prev) => [...prev, { role: 'assistant', content: 'Ошибка' }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" gutterBottom sx={{ fontWeight: 'bold' }}>
          🛠️ Интерактивный подборщик товаров
        </Typography>
        {stats && (
          <Typography variant="body2" color="text.secondary">
            {stats.total_documents} каталогов • {stats.total_products} товаров •{stats.categories} категорий
          </Typography>
        )}
      </Box>

      <Tabs value={tabValue} onChange={(e, val) => setTabValue(val)} sx={{ mb: 2 }}>
        <Tab icon={<SearchIcon />} label="Поиск" />
        <Tab icon={<TuneIcon />} label="Фильтры" />
        <Tab icon={<ChatIcon />} label="Вопросы" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card sx={{ p: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={8}>
                  <TextField
                    fullWidth
                    label="Поиск"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Button fullWidth variant="contained" onClick={handleSearch} disabled={loading}>
                    Поиск
                  </Button>
                </Grid>
              </Grid>
            </Card>
          </Grid>
          <Grid item xs={12} md={8}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {searchResults.map((product) => (
                <Card key={product.id} onClick={() => handleProductSelect(product)} sx={{ cursor: 'pointer' }}>
                  <CardContent>
                    <Typography variant="h6">{product.title}</Typography>
                    {product.sku && <Chip label={`SKU: ${product.sku}`} size="small" />}
                    <Typography variant="body2">{product.description}</Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            {selectedProduct && (
              <>
                <Typography variant="h6" gutterBottom>
                  Похожие товары
                </Typography>
                {recommendations.map((p) => (
                  <Card key={p.id} sx={{ mb: 1, cursor: 'pointer' }} onClick={() => handleProductSelect(p)}>
                    <CardContent sx={{ p: 1 }}>
                      <Typography variant="subtitle2">{p.title}</Typography>
                    </CardContent>
                  </Card>
                ))}
              </>
            )}
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Card sx={{ p: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Фильтры
              </Typography>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Категория</InputLabel>
                <Select value={selectedCategory} label="Категория" onChange={(e) => setSelectedCategory(e.target.value)}>
                  <MenuItem value="">Все</MenuItem>
                  {categories.map((cat) => (
                    <MenuItem key={cat} value={cat}>
                      {cat}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <Typography>Давление (bar)</Typography>
              <Slider value={pressureRange} onChange={(e, val: any) => setPressureRange(val)} min={0} max={100} />
            </Grid>
            <Grid item xs={12}>
              <Typography>Диаметр (mm)</Typography>
              <Slider value={diameterRange} onChange={(e, val: any) => setDiameterRange(val)} min={0} max={100} />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Материал"
                value={selectedMaterial}
                onChange={(e) => setSelectedMaterial(e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <Button fullWidth variant="contained" onClick={handleFilter}>
                Применить
              </Button>
            </Grid>
          </Grid>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Card sx={{ p: 2, height: '600px', display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ flex: 1, overflowY: 'auto', mb: 2, p: 2, backgroundColor: '#f5f5f5' }}>
            {chatMessages.map((msg, idx) => (
              <Box
                key={idx}
                sx={{
                  mb: 2,
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <Paper
                  sx={{
                    p: 2,
                    maxWidth: '70%',
                    backgroundColor: msg.role === 'user' ? '#1976d2' : '#e0e0e0',
                    color: msg.role === 'user' ? 'white' : 'black',
                  }}
                >
                  <Typography variant="body2">{msg.content}</Typography>
                </Paper>
              </Box>
            ))}
            <div ref={chatEndRef} />
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField fullWidth placeholder="Введите вопрос..." value={chatInput} onChange={(e) => setChatInput(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleChatSend()} />
            <Button variant="contained" onClick={handleChatSend} disabled={chatLoading}>
              Отправить
            </Button>
          </Box>
        </Card>
      </TabPanel>
    </Container>
  );
}
