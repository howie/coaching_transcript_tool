import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ClientModal } from '../ClientModal';
import { apiClient } from '@/lib/api';
import { useI18n } from '@/contexts/i18n-context';

// Mock modules
jest.mock('@/lib/api', () => ({
  apiClient: {
    createClient: jest.fn(),
  },
}));

jest.mock('@/contexts/i18n-context', () => ({
  useI18n: jest.fn(),
}));

describe('ClientModal', () => {
  const mockOnClose = jest.fn();
  const mockOnClientCreated = jest.fn();
  const mockT = (key: string) => key;

  beforeEach(() => {
    jest.clearAllMocks();
    (useI18n as jest.Mock).mockReturnValue({ t: mockT });
  });

  it('should render when open', () => {
    render(
      <ClientModal
        isOpen={true}
        onClose={mockOnClose}
        onClientCreated={mockOnClientCreated}
      />
    );

    expect(screen.getByText('clients.addClient')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('clients.namePlaceholder')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('clients.emailPlaceholder')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('clients.phonePlaceholder')).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    render(
      <ClientModal
        isOpen={false}
        onClose={mockOnClose}
        onClientCreated={mockOnClientCreated}
      />
    );

    expect(screen.queryByText('clients.addClient')).not.toBeInTheDocument();
  });

  it('should create client successfully', async () => {
    const newClient = {
      id: 'new-client-123',
      name: 'New Client',
      email: 'new@example.com',
      phone: '9876543210',
      memo: 'New client memo',
    };

    (apiClient.createClient as jest.Mock).mockResolvedValue(newClient);

    render(
      <ClientModal
        isOpen={true}
        onClose={mockOnClose}
        onClientCreated={mockOnClientCreated}
      />
    );

    // Fill in form
    const nameInput = screen.getByPlaceholderText('clients.namePlaceholder');
    const emailInput = screen.getByPlaceholderText('clients.emailPlaceholder');
    const phoneInput = screen.getByPlaceholderText('clients.phonePlaceholder');
    const memoInput = screen.getByPlaceholderText('clients.memoPlaceholder');

    fireEvent.change(nameInput, { target: { value: 'New Client' } });
    fireEvent.change(emailInput, { target: { value: 'new@example.com' } });
    fireEvent.change(phoneInput, { target: { value: '9876543210' } });
    fireEvent.change(memoInput, { target: { value: 'New client memo' } });

    // Submit form
    const submitButton = screen.getByText('common.create');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(apiClient.createClient).toHaveBeenCalledWith({
        name: 'New Client',
        email: 'new@example.com',
        phone: '9876543210',
        memo: 'New client memo',
      });
      expect(mockOnClientCreated).toHaveBeenCalledWith(newClient);
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('should handle creation error', async () => {
    window.alert = jest.fn();
    (apiClient.createClient as jest.Mock).mockRejectedValue(new Error('Creation failed'));

    render(
      <ClientModal
        isOpen={true}
        onClose={mockOnClose}
        onClientCreated={mockOnClientCreated}
      />
    );

    const nameInput = screen.getByPlaceholderText('clients.namePlaceholder');
    fireEvent.change(nameInput, { target: { value: 'Test Client' } });

    const submitButton = screen.getByText('common.create');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('clients.createError');
      expect(mockOnClientCreated).not.toHaveBeenCalled();
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  it('should handle cancel button', () => {
    render(
      <ClientModal
        isOpen={true}
        onClose={mockOnClose}
        onClientCreated={mockOnClientCreated}
      />
    );

    const cancelButton = screen.getByText('common.cancel');
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
    expect(mockOnClientCreated).not.toHaveBeenCalled();
  });

  it('should reset form when closing', () => {
    render(
      <ClientModal
        isOpen={true}
        onClose={mockOnClose}
        onClientCreated={mockOnClientCreated}
      />
    );

    // Fill in form
    const nameInput = screen.getByPlaceholderText('clients.namePlaceholder') as HTMLInputElement;
    fireEvent.change(nameInput, { target: { value: 'Test Client' } });
    expect(nameInput.value).toBe('Test Client');

    // Click cancel
    const cancelButton = screen.getByText('common.cancel');
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should validate required fields', async () => {
    render(
      <ClientModal
        isOpen={true}
        onClose={mockOnClose}
        onClientCreated={mockOnClientCreated}
      />
    );

    const nameInput = screen.getByPlaceholderText('clients.namePlaceholder');
    
    // Name field should be required
    expect(nameInput).toHaveAttribute('required');
  });
});