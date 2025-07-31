import { Container, Flex, Heading, Text, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"

import { DemoService } from "@/client"
import AddOrder from "@/components/Orders/AddOrder"

const ordersSearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 10

function getOrdersQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      DemoService.readOrders({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    queryKey: ["orders", { page }],
  }
}

export const Route = createFileRoute("/_layout/orders")({
  component: Orders,
  validateSearch: (search) => ordersSearchSchema.parse(search),
})

function Orders() {
  const { page } = Route.useSearch()

  const { data, isLoading } = useQuery({
    ...getOrdersQueryOptions({ page }),
  })

  if (isLoading) {
    return (
      <Container maxW="full" py={4}>
        <Text>Loading orders...</Text>
      </Container>
    )
  }

  return (
    <Container maxW="full" py={4}>
      <VStack gap={4} align="stretch">
        <Flex justify="space-between" align="center">
          <Heading size="lg" textAlign={{ base: "center", md: "left" }}>
            Orders Management
          </Heading>
          <AddOrder />
        </Flex>

        <Text>Total orders: {data?.count || 0}</Text>

        {data?.data && data.data.length > 0 ? (
          <VStack gap={3} align="stretch">
            {data.data.map((order) => (
              <Flex
                key={order.id}
                p={4}
                borderWidth={1}
                borderRadius="md"
                justify="space-between"
                align="center"
              >
                <VStack align="start" gap={1}>
                  <Text fontWeight="bold">Order #{order.id}</Text>
                  <Text fontSize="sm" color="gray.600">
                    Status: {order.status}
                  </Text>
                  <Text fontSize="sm">
                    Total: ${order.total_amount} | Items:{" "}
                    {order.order_items?.length || 0}
                  </Text>
                  {order.notes && (
                    <Text fontSize="sm" color="gray.500">
                      Notes: {order.notes}
                    </Text>
                  )}
                </VStack>
              </Flex>
            ))}
          </VStack>
        ) : (
          <Text>No orders found</Text>
        )}
      </VStack>
    </Container>
  )
}
