import { useState } from 'react'
import { DEFAULT_CITY_IMAGE, getCityImage } from '../../utils/cityImages'

interface Props {
  city: string
  alt?: string
  className?: string
}

export default function CityImage({ city, alt, className }: Props) {
  const [src, setSrc] = useState(() => getCityImage(city))

  return (
    <img
      src={src}
      alt={alt ?? city}
      loading="lazy"
      decoding="async"
      onError={() => {
        if (src !== DEFAULT_CITY_IMAGE) setSrc(DEFAULT_CITY_IMAGE)
      }}
      className={className}
    />
  )
}
