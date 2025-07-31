import {
  Container,
  Flex,
  HStack,
  Heading,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"

import { DemoService } from "@/client"
import AddProduct from "@/components/Products/AddProduct"
import DeleteProduct from "@/components/Products/DeleteProduct"
import EditProduct from "@/components/Products/EditProduct"

const productsSearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 10

function getProductsQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      DemoService.readProducts({
        skip: (page - 1) * PER_PAGE,
        limit: PER_PAGE,
      }),
    queryKey: ["products", { page }],
  }
}

export const Route = createFileRoute("/_layout/products")({
  component: Products,
  validateSearch: (search) => productsSearchSchema.parse(search),
})

function Products() {
  const { page } = Route.useSearch()

  const { data, isLoading } = useQuery({
    ...getProductsQueryOptions({ page }),
  })

  if (isLoading) {
    return (
      <Container maxW="full" py={4}>
        <Text>Loading products...</Text>
      </Container>
    )
  }

  return (
    <Container maxW="full" py={4}>
      <VStack gap={4} align="stretch">
        <Flex justify="space-between" align="center">
          <Heading size="lg" textAlign={{ base: "center", md: "left" }}>
            Products Management
          </Heading>
          <AddProduct />
        </Flex>

        <Text>Total products: {data?.count || 0}</Text>

        {data?.data && data.data.length > 0 ? (
          <VStack gap={3} align="stretch">
            {data.data.map((product) => (
              <Flex
                key={product.id}
                p={4}
                borderWidth={1}
                borderRadius="md"
                justify="space-between"
                align="center"
              >
                <VStack align="start" gap={1}>
                  <Text fontWeight="bold">{product.name}</Text>
                  <Text fontSize="sm" color="gray.600">
                    {product.description || "No description"}
                  </Text>
                  <Text fontSize="sm">
                    Price: ${product.price} | Stock: {product.stock_quantity} |
                    Category: {product.category}
                  </Text>
                  <Text
                    fontSize="xs"
                    color={product.is_active ? "green.500" : "red.500"}
                  >
                    {product.is_active ? "Active" : "Inactive"}
                  </Text>
                </VStack>
                <HStack gap={2}>
                  <EditProduct product={product} />
                  <DeleteProduct product={product} />
                </HStack>
              </Flex>
            ))}
          </VStack>
        ) : (
          <Text>No products found</Text>
        )}
      </VStack>
    </Container>
  )
}
