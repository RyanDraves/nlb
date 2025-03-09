module HydProgressBar

using ProgressMeter: @showprogress
using HTTP
using JSON

export ProgressBar, fancyprogress

mutable struct ProgressBar
    label::String
    endpoint::String
    max_value::Union{Nothing,Int}
    value::Int
    status::Union{Nothing,String}
end

function ProgressBar(label::String; endpoint::String="http://localhost:3000/api/progress",
    max_value::Union{Nothing,Int}=nothing,
    value::Int=0,
    status::Union{Nothing,String}=nothing)

    return ProgressBar(label, endpoint, max_value, value, status)
end

function update_status!(pb::ProgressBar; status::Union{Nothing,String}=nothing)
    local_data = Dict(
        "label" => pb.label,
        "value" => pb.value,
        "max_value" => pb.max_value,
        "status" => status === nothing ? "" : status
    )

    json_body = JSON.json(local_data)

    response = HTTP.post(pb.endpoint,
        headers=Dict("Content-Type" => "application/json"),
        body=json_body)

    @assert response.status == 200
end

function update_value!(pb::ProgressBar; value::Int)
    pb.value = value
    update_status!(pb)
end

function fancyprogress(f::Function, pb::ProgressBar, items)
    pb.max_value = length(items)
    @showprogress for (i, x) in enumerate(items)
        update_value!(pb, value=i)
        f(x)
    end
end

pb = ProgressBar("Julia Progress", max_value=100)
fancyprogress(pb, 1:100) do x
    update_status!(pb, status="Processing $x")
    sleep(0.1)
end

end
