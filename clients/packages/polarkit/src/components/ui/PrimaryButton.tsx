import React from 'react'
import { classNames } from '../../utils/dom'

const LargeLoadingSpinner = (props: { disabled: boolean }) => {
  const classes = classNames(
    props.disabled
      ? 'fill-gray-300 text-gray-200 dark:fill-gray-600 dark:text-gray-400'
      : 'fill-white text-blue-300',
    'h-6 w-6 animate-spin',
  )

  return (
    <>
      <div role="status">
        <svg
          aria-hidden="true"
          className={classes}
          viewBox="0 0 100 101"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
            fill="currentColor"
          />
          <path
            d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
            fill="currentFill"
          />
        </svg>
      </div>
    </>
  )
}

const TinyLoadingSpinner = (props: { disabled: boolean }) => {
  const classes = classNames(
    props.disabled
      ? 'fill-gray-300 text-gray-200 dark:fill-gray-600 dark:text-gray-400'
      : 'fill-white text-blue-300',
    'h-4 w-4 animate-spin',
  )

  return (
    <>
      <div role="status">
        <svg
          aria-hidden="true"
          className={classes}
          viewBox="0 0 100 101"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
            fill="currentColor"
          />
          <path
            d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
            fill="currentFill"
          />
        </svg>
      </div>
    </>
  )
}

type Color = 'blue' | 'gray' | 'red' | 'green' | 'lightblue'
type Size = 'normal' | 'small' | 'smaller'

type ButtonProps = {
  children: React.ReactNode
  href?: string
  color: Color
  fullWidth: boolean
  size: Size
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void
} & typeof defaultProps

const defaultProps = {
  disabled: false,
  loading: false,
  color: 'blue' as Color,
  size: 'normal' as Size,
  fullWidth: true,
  classNames: '',
}

const bg = (color: Color, loading: boolean, disabled: boolean) => {
  if (disabled) {
    return 'bg-gray-200/75 dark:bg-gray-700/75'
  }

  if (loading) {
    switch (color) {
      case 'blue':
        return 'bg-blue-400'
      case 'lightblue':
        return 'bg-blue-400'
      case 'red':
        return 'bg-red-400'
      case 'green':
        return 'bg-green-400'
      case 'gray':
        return 'bg-gray-400'
    }
  }

  switch (color) {
    case 'blue':
      return 'bg-blue-600 hover:bg-blue-500'
    case 'lightblue':
      return 'bg-blue-500 hover:bg-blue-600'
    case 'red':
      return 'bg-red-600 hover:bg-red-500'
    case 'green':
      return 'bg-green-600 hover:bg-green-500'
    case 'gray':
      return 'bg-gray-600 hover:bg-gray-500'
  }
}

const text = (color: Color, loading: boolean, disabled: boolean) => {
  if (disabled) {
    return 'text-gray-400 dark:text-gray-300'
  }
  if (loading) {
    return 'text-gray-400'
  }
  if (loading) {
    return 'text-white'
  }
  return 'text-white'
}

const size = (size: Size) => {
  if (size === 'small') {
    return 'px-3 py-1.5 min-h-6 text-sm font-medium '
  }
  return 'px-5 py-2 min-h-6 text-sm font-medium '
}

const PrimaryButton = (props: ButtonProps) => {
  const disabled = props.disabled ? props.disabled : false
  let classes = classNames(
    bg(props.color, props.loading, disabled),
    text(props.color, props.loading, disabled),
    size(props.size),
    props.fullWidth ? 'w-full' : '',
    'rounded-lg  text-center  inline-flex items-center space-x-2 transition-colors duration-100 justify-center whitespace-nowrap',
    props.classNames,
  )

  const spinnerOrPlaceholder = (): React.ReactNode => {
    if (props.loading) {
      if (props.size === 'normal') {
        return <LargeLoadingSpinner disabled={disabled} />
      } else {
        return <TinyLoadingSpinner disabled={disabled} />
      }
    }
    if (!props.loading) {
      if (props.size === 'normal') {
        return <div className="-mr-2 h-6 w-0"></div>
      } else {
        return <div className="-mr-2 h-4 w-0"></div>
      }
    }

    return null
  }

  return (
    <>
      <button className={classes} onClick={props.onClick} disabled={disabled}>
        {spinnerOrPlaceholder()}
        {!props.loading && props.children}
      </button>
    </>
  )
}

PrimaryButton.defaultProps = defaultProps

export default PrimaryButton

export const ThinButton = (props: ButtonProps) => {
  const disabled = props.disabled ? props.disabled : false
  let classes = classNames(
    bg(props.color, props.loading, disabled),
    text(props.color, props.loading, disabled),
    'rounded-md px-2 py-1 text-xs font-semibold transition-colors duration-100 h-6 flex whitespace-nowrap inline-flex',
  )

  if (props.href) {
    return (
      <>
        <a className={classes} href={props.href} target="_blank">
          {!props.loading && (
            <div className="h-4">{/* Same height as LoadingSpinner */}</div>
          )}
          {props.loading && <TinyLoadingSpinner disabled={disabled} />}
          {!props.loading && (
            <div className="flex space-x-1">{props.children}</div>
          )}
        </a>
      </>
    )
  }

  return (
    <>
      <button className={classes} onClick={props.onClick} disabled={disabled}>
        {!props.loading && (
          <div className="h-4">{/* Same height as LoadingSpinner */}</div>
        )}
        {props.loading && <TinyLoadingSpinner disabled={disabled} />}
        {!props.loading && (
          <div className="flex space-x-1">{props.children}</div>
        )}
      </button>
    </>
  )
}

ThinButton.defaultProps = defaultProps
