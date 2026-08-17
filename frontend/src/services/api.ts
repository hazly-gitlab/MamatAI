import axios from 'axios';

const API_BASE = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('jarvis_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authService = {
  async register(username: string, email: string, role: string = 'user') {
    const response = await apiClient.post('/auth/register', {
      username,
      email,
      role,
      password: 'DefaultPassword123!',
    });
    return response.data;
  },

  async login(username: string) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', 'DefaultPassword123!');

    const response = await apiClient.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    const data = response.data;
    localStorage.setItem('jarvis_token', data.access_token);
    localStorage.setItem('jarvis_username', data.username);
    localStorage.setItem('jarvis_role', data.role);
    return data;
  },

  logout() {
    localStorage.removeItem('jarvis_token');
    localStorage.removeItem('jarvis_username');
    localStorage.removeItem('jarvis_role');
  },

  getCurrentUser() {
    return {
      username: localStorage.getItem('jarvis_username'),
      role: localStorage.getItem('jarvis_role'),
      token: localStorage.getItem('jarvis_token'),
    };
  }
};

export const documentService = {
  async upload(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async list() {
    const response = await apiClient.get('/documents');
    return response.data;
  },

  async delete(id: number) {
    const response = await apiClient.delete(`/documents/${id}`);
    return response.data;
  }
};

export const conversationService = {
  async list() {
    const response = await apiClient.get('/conversations');
    return response.data;
  },

  async create(title: string = 'New Chat') {
    const response = await apiClient.post(`/conversations?title=${encodeURIComponent(title)}`);
    return response.data;
  },

  async delete(id: string) {
    const response = await apiClient.delete(`/conversations/${id}`);
    return response.data;
  },

  async getMessages(id: string) {
    const response = await apiClient.get(`/conversations/${id}/messages`);
    return response.data;
  },

  async confirmAction(actionId: string, approved: boolean) {
    const response = await apiClient.post(`/conversations/action/confirm?action_id=${actionId}&approved=${approved}`);
    return response.data;
  }
};
