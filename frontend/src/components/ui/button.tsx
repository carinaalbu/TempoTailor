import { type ButtonHTMLAttributes, forwardRef } from 'react'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary' | 'ghost' | 'destructive'
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'default', ...props }, ref) => {
    const base = 'inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-950 disabled:opacity-50 disabled:pointer-events-none'
    const variants = {
      default: 'bg-green-600 text-white hover:bg-green-500 focus:ring-green-500',
      secondary: 'bg-gray-800 text-white hover:bg-gray-700 focus:ring-gray-500',
      ghost: 'hover:bg-gray-800 focus:ring-gray-500',
      destructive: 'bg-red-600 text-white hover:bg-red-500 focus:ring-red-500',
    }
    return (
      <button
        ref={ref}
        className={`${base} ${variants[variant]} ${className}`}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'
export { Button }
