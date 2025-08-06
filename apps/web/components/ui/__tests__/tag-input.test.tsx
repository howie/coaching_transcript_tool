import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TagInput } from '../tag-input';

describe('TagInput', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  it('renders empty tag input correctly', () => {
    render(<TagInput value="" onChange={mockOnChange} />);
    
    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('placeholder', '輸入後按 Enter 新增標籤');
  });

  it('displays existing tags from comma-separated string', () => {
    render(<TagInput value="職涯發展, 人際關係, 領導力" onChange={mockOnChange} />);
    
    expect(screen.getByText('職涯發展')).toBeInTheDocument();
    expect(screen.getByText('人際關係')).toBeInTheDocument();
    expect(screen.getByText('領導力')).toBeInTheDocument();
  });

  it('adds new tag when Enter is pressed', async () => {
    const user = userEvent.setup();
    render(<TagInput value="" onChange={mockOnChange} />);
    
    const input = screen.getByRole('textbox');
    await user.type(input, '新標籤');
    await user.keyboard('{Enter}');
    
    expect(mockOnChange).toHaveBeenCalledWith('新標籤');
  });

  it('adds new tag to existing tags', async () => {
    const user = userEvent.setup();
    render(<TagInput value="職涯發展" onChange={mockOnChange} />);
    
    const input = screen.getByRole('textbox');
    await user.type(input, '人際關係');
    await user.keyboard('{Enter}');
    
    expect(mockOnChange).toHaveBeenCalledWith('職涯發展, 人際關係');
  });

  it('removes tag when X button is clicked', async () => {
    const user = userEvent.setup();
    render(<TagInput value="職涯發展, 人際關係" onChange={mockOnChange} />);
    
    const removeButtons = screen.getAllByLabelText(/Remove .* tag/);
    await user.click(removeButtons[0]);
    
    expect(mockOnChange).toHaveBeenCalledWith('人際關係');
  });

  it('does not add duplicate tags', async () => {
    const user = userEvent.setup();
    render(<TagInput value="職涯發展" onChange={mockOnChange} />);
    
    const input = screen.getByRole('textbox');
    await user.type(input, '職涯發展');
    await user.keyboard('{Enter}');
    
    expect(mockOnChange).not.toHaveBeenCalled();
  });

  it('trims whitespace from new tags', async () => {
    const user = userEvent.setup();
    render(<TagInput value="" onChange={mockOnChange} />);
    
    const input = screen.getByRole('textbox');
    await user.type(input, '  新標籤  ');
    await user.keyboard('{Enter}');
    
    expect(mockOnChange).toHaveBeenCalledWith('新標籤');
  });

  it('removes last tag when backspace is pressed on empty input', async () => {
    const user = userEvent.setup();
    render(<TagInput value="職涯發展, 人際關係" onChange={mockOnChange} />);
    
    const input = screen.getByRole('textbox');
    await user.click(input);
    await user.keyboard('{Backspace}');
    
    expect(mockOnChange).toHaveBeenCalledWith('職涯發展');
  });

  it('adds tag on blur if input has value', async () => {
    const user = userEvent.setup();
    render(<TagInput value="" onChange={mockOnChange} />);
    
    const input = screen.getByRole('textbox');
    await user.type(input, '新標籤');
    await user.tab(); // This triggers blur
    
    expect(mockOnChange).toHaveBeenCalledWith('新標籤');
  });

  it('disables interaction when disabled prop is true', () => {
    render(
      <TagInput 
        value="職涯發展" 
        onChange={mockOnChange} 
        disabled={true}
      />
    );
    
    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
    
    // Remove button should not be present when disabled
    expect(screen.queryByLabelText(/Remove .* tag/)).not.toBeInTheDocument();
  });

  it('shows help text', () => {
    render(<TagInput value="" onChange={mockOnChange} />);
    
    expect(screen.getByText('輸入議題類型後按 Enter 新增標籤，點擊標籤旁的 × 可刪除')).toBeInTheDocument();
  });
});