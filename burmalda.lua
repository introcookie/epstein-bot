--[[
    BURMALDA SYSTEM v16.0
    MM2 Prank Bomb Double Jump
    Toggle: L | Bomb Key: G
--]]

local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local LocalPlayer = Players.LocalPlayer
local StarterGui = game:GetService("StarterGui")

local Enabled = false
local Char, Hum, Root, Backpack

local function UpdateCache()
    Char = LocalPlayer.Character
    Hum = Char and Char:FindFirstChildOfClass("Humanoid")
    Root = Char and Char:FindFirstChild("HumanoidRootPart")
    Backpack = LocalPlayer:FindFirstChild("Backpack")
end
UpdateCache()

LocalPlayer.CharacterAdded:Connect(function()
    task.wait(0.1)
    UpdateCache()
end)

LocalPlayer.CharacterRemoving:Connect(function()
    Char, Hum, Root = nil, nil, nil
end)

local function FindBomb()
    local function scan(c)
        if not c then return nil end
        for _, v in ipairs(c:GetChildren()) do
            if v:IsA("Tool") and v.Name:lower():find("bomb") then
                return v
            end
        end
        return nil
    end
    return scan(Backpack) or scan(Char) or scan(workspace)
end

local function Notify(title, text)
    StarterGui:SetCore("SendNotification", {
        Title = title,
        Text = text,
        Duration = 1.5,
    })
end

local function Execute()
    if not Enabled then return end
    
    local bomb = FindBomb()
    if not bomb then return end
    
    if bomb.Parent ~= Char and Hum then
        Hum:EquipTool(bomb)
        task.wait(0.2)
    end
    
    if Hum then
        Hum:ChangeState(Enum.HumanoidStateType.Jumping)
    end
    
    task.wait(0.2)
    
    if bomb and Root and Hum then
        local bombRef = bomb
        Hum:UnequipTools()
        task.wait(0.05)
        
        pcall(function()
            local dropPos = Root.Position + Vector3.new(0, -3, 0)
            bombRef.Parent = workspace
            if bombRef:FindFirstChild("Handle") then
                bombRef.Handle.CFrame = CFrame.new(dropPos)
                bombRef.Handle.Velocity = Vector3.new(0, -100, 0)
                bombRef.Handle.AssemblyLinearVelocity = Vector3.new(0, -100, 0)
            end
        end)
    end
    
    task.wait(0.35)
    
    if Root and Hum and Hum.Health > 0 then
        Root.Velocity = Vector3.new(Root.Velocity.X, 70, Root.Velocity.Z)
        Hum:ChangeState(Enum.HumanoidStateType.Jumping)
    end
end

UIS.InputBegan:Connect(function(input, gameProcessed)
    if gameProcessed then return end
    
    if input.KeyCode == Enum.KeyCode.L then
        Enabled = not Enabled
        Notify("Burmalda", Enabled and "Burmalda On" or "Burmalda Off")
    end
    
    if Enabled and input.KeyCode == Enum.KeyCode.G then
        task.spawn(Execute)
    end
end)

Notify("Burmalda", "L - ON/OFF | G - Double Jump")