import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';

interface ProductItem {
  id: string;
  title: string;
  sku?: string;
  description?: string;
  specs: Record<string, string>;
  category: string;
}

interface ProductDetailDialogProps {
  product: ProductItem | null;
  open: boolean;
  onClose: () => void;
}

export const ProductDetailDialog: React.FC<ProductDetailDialogProps> = ({
  product,
  open,
  onClose,
}) => {
  if (!product) return null;

  const specEntries = Object.entries(product.specs || {});

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{product.title}</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          {product.sku && (
            <Box sx={{ mb: 2 }}>
              <Chip label={`SKU: ${product.sku}`} />
            </Box>
          )}
          <Chip label={product.category} sx={{ mb: 2 }} />

          {product.description && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Описание
              </Typography>
              <Typography variant="body2">{product.description}</Typography>
            </Box>
          )}

          {specEntries.length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Спецификации
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Параметр</TableCell>
                      <TableCell>Значение</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {specEntries.map(([key, value]) => (
                      <TableRow key={key}>
                        <TableCell>{key}</TableCell>
                        <TableCell>{value}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Закрыть</Button>
      </DialogActions>
    </Dialog>
  );
};
