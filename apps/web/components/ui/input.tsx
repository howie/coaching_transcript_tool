import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Input: React.FC<InputProps> = ({ className = '', ...props }) => {
  return (
    <input
      className={`w-full px-3 py-2 border border-border rounded-md bg-card text-foreground placeholder:text-placeholder focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent ${className}`}
      {...props}
    />
  );
};