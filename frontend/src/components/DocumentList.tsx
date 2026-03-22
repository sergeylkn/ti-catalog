import React from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';

interface DocumentInfo {
  id: string;
  filename: string;
  category: string;
  pages: number;
}

interface DocumentListProps {
  documents: DocumentInfo[];
  loading: boolean;
}

export const DocumentList: React.FC<DocumentListProps> = ({ documents, loading }) => {
  if (loading) {
    return <Typography>Загрузка документов...</Typography>;
  }

  if (documents.length === 0) {
    return <Typography color="textSecondary">Документы не найдены</Typography>;
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Доступные каталоги ({documents.length})
      </Typography>
      <List>
        {documents.map((doc) => (
          <ListItem key={doc.id} divider>
            <ListItemText
              primary={doc.filename}
              secondary={`${doc.category} • ${doc.pages} страниц`}
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};
