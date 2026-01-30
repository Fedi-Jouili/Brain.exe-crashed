# Multimodal Search Feature

## Overview

The PriceSense API now supports **multimodal search** combining text queries with image uploads for enhanced visual similarity matching using CLIP embeddings.

## Endpoint

```
POST /api/search
Content-Type: multipart/form-data
```

## Parameters

| Parameter      | Type        | Required | Description                             |
| -------------- | ----------- | -------- | --------------------------------------- |
| `query`        | string      | Yes      | Text search query                       |
| `max_results`  | integer     | No       | Maximum number of results (default: 10) |
| `user_profile` | JSON string | No       | User profile with financial info        |
| `image`        | File        | No       | Product image for visual search         |

## Supported Image Formats

- **JPEG** (.jpg, .jpeg)
- **PNG** (.png)
- **WebP** (.webp)

**Max file size**: 10MB

## How It Works

### Text-Only Search (Traditional)
```bash
curl -X POST http://localhost:8000/api/search \
  -F "query=gaming laptop under $800" \
  -F "max_results=10" \
  -F 'user_profile={"user_id": "USER123", "monthly_income": 5000, "credit_score": 720}'
```

Response metadata:
```json
{
  "metadata": {
    "multimodal": false,
    "search_mode": "text_only"
  }
}
```

### Multimodal Search (Text + Image)
```bash
curl -X POST http://localhost:8000/api/search \
  -F "query=phones like this under $500" \
  -F "image=@my_phone.jpg" \
  -F "max_results=10" \
  -F 'user_profile={"user_id": "USER123", "monthly_income": 5000, "credit_score": 720}'
```

Response metadata:
```json
{
  "metadata": {
    "multimodal": true,
    "search_mode": "multimodal"
  }
}
```

## Technical Details

### CLIP Embeddings

- **Model**: OpenAI CLIP ViT-B/32
- **Embedding dimension**: 512
- **Weighting**: 70% text + 30% image (normalized)

### Image Processing Pipeline

1. **Validation**: Check format (JPG/PNG/WebP) and size (<10MB)
2. **Upload**: Save to temporary file
3. **Embedding**: Generate 512-dimensional CLIP embedding
4. **Cleanup**: Remove temporary file
5. **Search**: Combine with text embedding (70/30 ratio)

### Agent 1 Integration

The multimodal embedding is passed to **Agent 1 (Discovery)** via the workflow state:

```python
workflow(
    query=query,
    user_profile=user_profile_obj,
    image_embedding=image_embedding  # 512-dim array
)
```

Agent 1 combines embeddings:
```python
def _generate_query_embedding(self, query: str, image_embedding: list = None):
    if image_embedding:
        text_embedding = self.embedder.embed_text(query)
        combined = 0.7 * text_embedding + 0.3 * np.array(image_embedding)
        return (combined / np.linalg.norm(combined)).tolist()
    else:
        return self.embedder.embed_text(query).tolist()
```

### Caching

- **Text-only cache key**: `search:{query_hash}:{user_id}`
- **Multimodal cache key**: `search:{query_hash}:{user_id}:img`

Different cache keys ensure text vs multimodal searches don't collide.

## Use Cases

### 1. Visual Similarity Search
User wants products that **look like** a reference image:
```bash
curl -X POST http://localhost:8000/api/search \
  -F "query=similar products" \
  -F "image=@reference.jpg"
```

### 2. Style Matching
User wants products matching a specific aesthetic:
```bash
curl -X POST http://localhost:8000/api/search \
  -F "query=minimalist desk setup" \
  -F "image=@minimalist_desk.jpg"
```

### 3. Color Matching
User wants products in a specific color:
```bash
curl -X POST http://localhost:8000/api/search \
  -F "query=furniture in this color" \
  -F "image=@blue_furniture.jpg"
```

## Error Handling

### Invalid Image Format
```json
{
  "detail": "Unsupported image format. Supported: image/jpeg, image/png, image/webp"
}
```
**HTTP 400 Bad Request**

### Image Too Large
```json
{
  "detail": "Image too large. Maximum size: 10MB"
}
```
**HTTP 400 Bad Request**

### Missing Image File
If `image` parameter is empty or null, the search falls back to text-only mode (no error).

## Testing

Run integration tests:
```bash
pytest backend/tests/test_multimodal_search.py -v -m integration
```

Test coverage:
- ✅ Text-only search (backward compatibility)
- ✅ Multimodal search (text + image)
- ✅ Image format validation (JPG/PNG/WebP)
- ✅ Image size validation (<10MB)
- ✅ Metadata flags (multimodal, search_mode)
- ✅ Cache key differentiation
- ✅ Agent 1 embedding integration

## Performance

- **Image upload**: ~50-100ms (network dependent)
- **CLIP embedding**: ~200-300ms (CPU) or ~50-100ms (GPU)
- **Total overhead**: ~300-400ms for multimodal vs text-only

## Example Python Client

```python
import requests

# Text + Image search
with open("product_image.jpg", "rb") as img_file:
    response = requests.post(
        "http://localhost:8000/api/search",
        data={
            "query": "phones like this under $500",
            "max_results": 10,
            "user_profile": '{"user_id": "USER123", "monthly_income": 5000, "credit_score": 720}'
        },
        files={"image": ("product.jpg", img_file, "image/jpeg")}
    )

data = response.json()
print(f"Multimodal: {data['metadata']['multimodal']}")
print(f"Results: {len(data['recommendations'])} products")
```

## Frontend Integration (React Example)

```javascript
const searchWithImage = async (query, imageFile) => {
  const formData = new FormData();
  formData.append('query', query);
  formData.append('max_results', 10);
  formData.append('image', imageFile);
  formData.append('user_profile', JSON.stringify({
    user_id: 'USER123',
    monthly_income: 5000,
    credit_score: 720
  }));

  const response = await fetch('http://localhost:8000/api/search', {
    method: 'POST',
    body: formData
  });

  const data = await response.json();
  console.log('Multimodal search:', data.metadata.multimodal);
  return data;
};
```

## Limitations

1. **Image quality**: Low-resolution images (<100x100) may not produce accurate embeddings
2. **Object detection**: CLIP embeddings capture overall image style, not specific object locations
3. **File size**: 10MB limit to prevent memory issues
4. **Supported formats**: Only JPG, PNG, WebP (no GIF, BMP, TIFF)

## Future Enhancements

- [ ] Multiple image upload (e.g., "products that combine features from these 3 images")
- [ ] Image cropping/region-of-interest selection
- [ ] GPU acceleration for CLIP embeddings
- [ ] Image preprocessing (resize, normalize) before embedding
- [ ] Support for more formats (GIF, SVG)
